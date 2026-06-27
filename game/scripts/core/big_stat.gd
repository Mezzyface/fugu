class_name BigStat
extends RefCounted
## Big-number stat value: `mantissa * 10 ^ magnitude`.
##
## Ported 1:1 from the Python prototype's frozen `BigStat` dataclass
## (`prototype/game.py`). Keeps mantissa in the half-open range [0, 1000) once
## normalized so late-game numbers stay readable without overflowing. Instances
## are treated as immutable — every operation returns a new `BigStat`.

var mantissa: int
var magnitude: int


func _init(p_mantissa: int, p_magnitude: int = 0) -> void:
	mantissa = p_mantissa
	magnitude = p_magnitude


## Returns an equivalent value with mantissa in [0, 1000) and a non-negative
## magnitude. A non-positive mantissa collapses to the canonical zero (`0e0`).
func normalized() -> BigStat:
	var m := maxi(0, mantissa)
	if m == 0:
		return BigStat.new(0, 0)
	var mag := maxi(0, magnitude)
	while m >= 1000:
		m = _floor_div(m, 10)
		mag += 1
	return BigStat.new(m, mag)


## Multiplies by `numerator / denominator` (denominator defaults to 100, i.e. a
## percentage). Borrows from the magnitude when the scaled mantissa would floor
## to zero so value is preserved across magnitudes. A non-positive denominator is
## invalid (the prototype raised `ValueError`); here it pushes an error and
## returns the canonical zero.
func scale(numerator: int, denominator: int = 100) -> BigStat:
	if denominator <= 0:
		push_error("scale denominator must be positive, got %d" % denominator)
		return BigStat.new(0, 0)
	var m := mantissa * numerator
	var mag := magnitude
	while m > 0 and m < denominator and mag > 0:
		m *= 10
		mag -= 1
	return BigStat.new(_floor_div(m, denominator), mag).normalized()


## Adds two values, aligning magnitudes first. When the gap is large enough the
## smaller operand is negligible and the larger is returned unchanged.
func add(other: BigStat) -> BigStat:
	var left := normalized()
	var right := other.normalized()
	if left.magnitude == right.magnitude:
		return BigStat.new(left.mantissa + right.mantissa, left.magnitude).normalized()
	var high := left if left.magnitude > right.magnitude else right
	var low := right if left.magnitude > right.magnitude else left
	var gap := high.magnitude - low.magnitude
	if gap > 6:
		return high
	var divisor := 1
	for _i in gap:
		divisor *= 10
	return BigStat.new(high.mantissa + _floor_div(low.mantissa, divisor), high.magnitude).normalized()


func _to_string() -> String:
	return "%de%d" % [mantissa, magnitude]


## Floor division matching Python's `//` (rounds toward negative infinity),
## unlike GDScript's `/` which truncates toward zero.
static func _floor_div(a: int, b: int) -> int:
	var q := a / b
	if a % b != 0 and (a < 0) != (b < 0):
		q -= 1
	return q
