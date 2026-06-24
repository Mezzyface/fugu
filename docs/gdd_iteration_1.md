# Hybrid Gacha RPG GDD - Iteration 1

## Vision
A collection RPG where characters are obtained through permanent standalone banners, trained through roguelike dungeon runs, then frozen into an inheritance pool that recursively powers future runs into extreme exponential stat growth.

## Pillars

### 1. Permanent Banner Gacha
- Each character owns a standalone banner.
- New characters are added permanently, never replacing older banners.
- A yearly featured schedule highlights subsets of banners for discovery bonuses, but all unlocked permanent banners remain rollable when available in the annual cycle.
- No limited-time exclusivity.
- RESOLVED: the banner system is characters-only in iteration 1. Cosmetics and quality-of-life items are a separate, later system — they do not share pity, shards, or resonance with character banners, and are out of scope until iteration 1's character loop is validated.

#### Banner Rules
- Base rarity rates:
  - Common: 79.5%
  - Rare: 15%
  - Epic: 4%
  - Legendary: 1.5%
- Soft pity starts at 70 pulls without Legendary, then the Legendary chance ramps by a discoverable per-pull increment (4.5% in iteration 1) until hard pity.
- Hard pity guarantees the banner character at 90 pulls.
- Duplicate pulls grant Shards.
- Shards upgrade resonance nodes, not raw stats, to avoid mandatory duplicate power cliffs.
- Iteration 1 resonance track:
  - 20 shards: Origin Story.
  - 40 shards: Signature Skill Variant.
  - 80 shards: Alternate Portrait.
  - 120 shards: Lineage Title.
- Resonance is capped at 4 nodes in the prototype; spending shards never changes base stats.

#### Annual Rotation Model
- The year is divided into 52 weekly slots.
- Each week features a group of permanent banners.
- Featured means discounted pity counter and bonus shard rate, not availability exclusivity.
- Iteration 1 prototype featured tuning:
  - Soft pity starts at 60 pulls instead of 70.
  - Hard pity guarantees the banner character at 80 pulls instead of 90.
  - Featured duplicate shards are increased to 15 for Legendary pulls and 2 for non-Legendary pulls.
- A Day 1 player sees every current character featured at least once per year.

### 2. Training Loop
A run starts by choosing:
- Base character or class.
- Optional inherited frozen ancestor.
- Training route: Balanced, Boss Rush, Skill Hunt, or Deep Scaling.

#### Run Structure
- 12 floors per standard run.
- Floors contain encounters: combat, event, elite, boss, shrine, rest.
- Every 4th floor is a boss gate.
- Clearing encounters grants XP, temporary run relics, skill mutations, and stat growth.
- Every run produces a Frozen Echo, even on a floor-1 failure (always-echo rule).
- Each route has a deterministic encounter pattern (by floor index) so the same route always presents the same kind sequence; the failed floor's encounter is recorded too, so a `RunResult` always has one more encounter than `floors_cleared` on a non-victory.

#### Boss Gate Checkpoints (Decided)
- Checkpoints are aligned to boss gates: floors 4 / 8 / 12.
- Checkpoint rewards are banked instantly when a boss gate is cleared and kept even if the run later fails.
- Rewards escalate per boss tier so the next boss gate is always worth pushing for:
  - Shards: `15 * 2^(tier-1)` (15, 30, 60).
  - Relic rolls: `tier` (1, 2, 3).
  - Echo quality bonus: `+20% * tier`, applied to the frozen echo's stats.
- Echo strength scales with the highest boss gate banked: a failed early run yields a weak echo; a full clear yields a much stronger one.
- This makes always-echo safe for progression while turning boss gates into the main push-your-luck milestones.

#### Instability Dividend (Decided)
- Instability is no longer a pure penalty; it is a risk/reward lever.
- Inherited power raises instability, which increases run difficulty (as before) but now also pays a shard dividend.
- The dividend is banked only when a boss-gate checkpoint is cleared: `instability * 5 * tier` shards per checkpoint.
- Because it rides on checkpoints, a run that fails before any boss gate forfeits the dividend entirely, so high-instability lineages are a genuine push-your-luck gamble rather than a flat tax.
- Stable (non-inherited) runs have zero instability and therefore zero dividend, keeping early game clean.

#### Relic Forge (Decided)
- Relic rolls earned at boss-gate checkpoints (and from echo exchanges) are spent in the Relic Forge, giving the currency a sink.
- Each roll produces one relic with a weighted rarity and a single boosted stat (`hp`, `atk`, `def`, or `spd`).
- Iteration 1 forge weights and bonuses:
  - Common: 60% chance, 8% stat bonus.
  - Rare: 25% chance, 15% stat bonus.
  - Epic: 12% chance, 25% stat bonus.
  - Legendary: 3% chance, 40% stat bonus.
- Relics multiply only their own stat; applying a relic never mutates the source stat block in place, keeping run state predictable.
- Forging is deterministic per seed for reproducible balance testing.

#### Stat Growth
Stats use two layers:
- Base stats: readable early-game values.
- Magnitude: exponent-like growth tier for late-game absurd numbers.

Displayed stat formula:
`display = mantissa * 10^magnitude`

Training increases mantissa often and magnitude rarely. This keeps numbers large without immediate overflow.

### 3. Inheritance & Exponential Scaling
At run end, the trained character becomes a Frozen Echo.
Future characters can inherit from up to two Echoes (RESOLVED — see Open Design Questions).

#### Echo Contents
- Final stat vector.
- Up to 3 frozen skills.
- Up to 2 traits.
- Lineage depth.
- Instability score.

#### EchoPool - Iteration 1
- Every completed or failed run can bank its Frozen Echo into the player's EchoPool.
- The pool has a capacity limit, but it does not auto-prune; if full, the player must delete or exchange echoes before banking more.
- Echoes can be favorited, protecting them from accidental deletion or exchange until unfavorited.
- Favorites are capped below total capacity (default `capacity - 1`) so the pool can never be fully locked; at least one echo always stays removable, keeping the always-echo rule safe.
- Echoes can receive sortable icon assignments such as `shield`, `star`, `skull`, `gold`, `boss`, or `favorite`.
- Echoes are ranked by a power score derived from stat magnitude, mantissa, skills, traits, lineage depth, and instability cost.
- Sorting supports power, icon, favorite state, source character, and lineage depth.
- Removal paths:
  - Manual delete for unwanted echoes.
  - Timed exchange events that consume one or many selected echoes (batch) for aggregated rewards such as essence, shards, and relic rolls, with an event multiplier.
- Parent selection in the prototype supports:
  - Best (up to two) available echoes overall.
  - Best (up to two) echoes filtered by source character.
- Iteration 1 uses up to two active parents per new run (RESOLVED — see Open Design Questions).

#### Inheritance Formula - Iteration 1
Each parent contributes independently and the contributions stack additively:
`child_stat = base_stat + sum_over_parents(floor(parent_stat * transfer_rate * diminishing_depth_factor))`

Magnitude contribution per parent:
`child_magnitude = base_magnitude + floor(parent_magnitude * magnitude_transfer_rate)`

Lineage depth with multiple parents is `max(parent_lineage_depths) + 1` — the deepest parent sets the depth, it is not summed across parents (otherwise depth, and therefore the diminishing-return penalty, would blow up just from breeding two shallow lines together).

Default tuning:
- Stat transfer rate: 25%.
- Magnitude transfer rate: 35%.
- Each parent's *own* lineage depth reduces its direct stat transfer by 8%, minimum 35% effectiveness — a deep parent contributes less per-parent than a shallow one, independent of how many parents are used.
- Instability accumulates per parent (each parent's inherited magnitude vs. class baseline) and sums across both parents, so two-parent runs are higher-instability, higher-difficulty, and higher-dividend than single-parent runs of the same depth.

#### Exponential Engine
The exponential loop comes from:
1. Train character.
2. Freeze high result.
3. Use echo as parent.
4. Child starts stronger, clears deeper scaling route.
5. New echo is much stronger.

#### Anti-Break Measures
- Big integers or mantissa/magnitude notation for all stat math.
- Maximum active inherited parents in iteration 1: two (`TrainingSimulator.max_parents`); passing more raises a `ValueError` rather than silently truncating the list.
- Trait stacking uses tags and caps.
- Instability can add run modifiers if power growth exceeds expected curve.

## Asset Direction
Provided project assets support a 2D fantasy prototype without needing new art for iteration 1.

### Asset Pack Mapping
- `Tiny Swords (Free Pack).zip`: early prototype units, buildings, and overworld combat spaces.
- `Tiny Swords (Enemy Pack).zip`: enemy families, elite variants, and boss silhouettes.
- `80_Monster_Packs.zip`: long-term bestiary expansion and rare dungeon encounters.
- `isle-of-lore-2-hex-tiles-regular-final.zip`: dungeon route boards and tactical map tiles.
- `isle-of-lore-2-hex-tiles-regular-borderless.zip`: cleaner procedural map variants.
- `isle-of-lore-2-rpg-item-icons-final.zip`: relics, currencies, shards, skill icons, and inheritance materials.
- `isle-of-lore-2-strategy-figures-final.zip`: party markers, encounter icons, and enemy tokens.
- `isle-of-lore-2-ui-pack-final.zip`: gacha panels, training screens, results, and inventory UI.
- `Kenney Game Assets All-in-1 3.5.0.zip`: broad fallback library for placeholders, sounds, UI, particles, and experiments.
- `tinypot_graybox-2d_basic.zip` and `tinypot_graybox-2d_extra.zip`: graybox layouts before final art hookup.
- `HoneyPigeon.zip` and `honeyblot_caps.zip`: candidate fonts for logo, banners, rarity labels, and result screens.

### Visual Target
- Readable top-down or board-based 2D fantasy.
- Cozy tactical map presentation contrasted with absurd number scaling.
- Gacha screens should feel archival/permanent rather than urgent or FOMO-driven.

## Prototype Scope
The prototype implements:
- Static character definitions.
- Permanent banner registry, deterministic pity simulation, featured-banner pity/shard bonuses, and resonance-node shard spending.
- Relic Forge that spends relic rolls into weighted-rarity stat relics, wired into the demo run flow so earned relic rolls are forged and applied to the latest echo's stats.
- Training run simulation over 12 floors.
- Frozen Echo creation.
- EchoPool banking, ranking, capacity limits, favorites, icons, delete, exchange, and parent selection.
- Two-parent inheritance.
- Big-number stat representation.
- Asset pack cataloging and recommended usage classification.

## QA Review - Iteration 1
- Hard pity must be tested with forced non-Legendary rolls because random early Legendary hits reset pity.
- RESOLVED: `BigStat.scale` previously truncated a small mantissa to zero when scaling down crossed a magnitude boundary (e.g. `5e2` scaled by 50% lost its value instead of becoming `2e2`/`3e2`); it now borrows magnitude before dividing so small values keep precision. Cross-magnitude `add` still drops a low operand more than 6 magnitudes below the high one, by design (negligible contribution).
- RESOLVED: inheritance now supports up to two parents (`EchoPool.best_parents`, `TrainingSimulator.start_stats`/`run`), which reads more like breeding than a single recursive prestige chain. Lineage depth is `max(parent depths) + 1`, not summed, to keep the diminishing-return curve from compounding just because two echoes were combined.
- EchoPool no longer auto-prunes; capacity pressure is resolved through manual deletion or exchange events, with favorites protected from accidental removal.
- RESOLVED: failure always creates an echo; boss-gate checkpoint rewards are banked and escalate, so deeper pushes are strictly more valuable.
- RESOLVED: instability is now a risk/reward mechanic — it raises difficulty but pays a checkpoint-gated shard dividend that is forfeited on a pre-checkpoint failure.
- Asset ZIPs are cataloged by metadata only; extraction and license review should happen before a playable build.

## Open Design Questions
1. RESOLVED: inheritance uses up to two parents in iteration 1 (not one, not an open ancestor pool). Each parent contributes independently and additively; lineage depth takes the deeper parent plus one rather than summing, so breeding two shallow lines doesn't artificially deepen the lineage penalty. A broader ancestor pool remains a possible future iteration.
2. RESOLVED: the gacha banner system monetizes characters only in iteration 1. Cosmetics and quality-of-life items are deferred to a separate system to be designed later, decoupled from character pity/shards/resonance.
3. RESOLVED: failed runs always create echoes; boss-gate checkpoint rewards incentivize pushing further.
4. RESOLVED: instability is a risk/reward multiplier — higher difficulty plus a checkpoint-gated shard dividend (`instability * 5 * tier`) that is lost on a pre-checkpoint failure.
