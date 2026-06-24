from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from random import Random
from typing import Dict, List, Optional, Sequence, Tuple


class Rarity(str, Enum):
    COMMON = "common"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"


@dataclass(frozen=True)
class BigStat:
    mantissa: int
    magnitude: int = 0

    def normalized(self) -> "BigStat":
        mantissa = max(0, self.mantissa)
        if mantissa == 0:
            return BigStat(0, 0)
        magnitude = max(0, self.magnitude)
        while mantissa >= 1000:
            mantissa //= 10
            magnitude += 1
        return BigStat(mantissa, magnitude)

    def scale(self, numerator: int, denominator: int = 100) -> "BigStat":
        if denominator <= 0:
            raise ValueError(f"scale denominator must be positive, got {denominator}")
        mantissa = self.mantissa * numerator
        magnitude = self.magnitude
        while 0 < mantissa < denominator and magnitude > 0:
            mantissa *= 10
            magnitude -= 1
        return BigStat(mantissa // denominator, magnitude).normalized()

    def add(self, other: "BigStat") -> "BigStat":
        left = self.normalized()
        right = other.normalized()
        if left.magnitude == right.magnitude:
            return BigStat(left.mantissa + right.mantissa, left.magnitude).normalized()
        high, low = (left, right) if left.magnitude > right.magnitude else (right, left)
        gap = high.magnitude - low.magnitude
        if gap > 6:
            return high
        return BigStat(high.mantissa + low.mantissa // (10**gap), high.magnitude).normalized()

    def __str__(self) -> str:
        return f"{self.mantissa}e{self.magnitude}"


Stats = Dict[str, BigStat]


@dataclass(frozen=True)
class CharacterDef:
    id: str
    name: str
    rarity: Rarity
    role: str
    base_stats: Stats
    skills: Tuple[str, ...]
    traits: Tuple[str, ...]


@dataclass
class BannerState:
    character_id: str
    pulls_since_legendary: int = 0
    shards: int = 0
    resonance_level: int = 0


@dataclass(frozen=True)
class ResonanceUpgrade:
    character_id: str
    level: int
    node: str
    cost: int
    remaining_shards: int


@dataclass(frozen=True)
class PullResult:
    rarity: Rarity
    character_id: str
    shards_gained: int
    pity_reset: bool


@dataclass(frozen=True)
class Relic:
    id: int
    name: str
    rarity: Rarity
    stat: str
    bonus_percent: int


@dataclass(frozen=True)
class FrozenEcho:
    source_character_id: str
    stats: Stats
    skills: Tuple[str, ...]
    traits: Tuple[str, ...]
    lineage_depth: int
    instability: int


@dataclass(frozen=True)
class CheckpointReward:
    floor: int
    tier: int
    shards: int
    relic_rolls: int
    echo_quality_bonus: int


@dataclass(frozen=True)
class EncounterRecord:
    floor: int
    kind: str
    power: int
    difficulty: int
    cleared: bool


@dataclass
class RunRewards:
    banked_shards: int = 0
    relic_rolls: int = 0
    highest_checkpoint_floor: int = 0
    echo_quality_percent: int = 100
    instability_dividend_shards: int = 0
    checkpoints: List[CheckpointReward] = field(default_factory=list)


@dataclass
class RunResult:
    floors_cleared: int
    victory: bool
    echo: FrozenEcho
    rewards: RunRewards = field(default_factory=RunRewards)
    log: List[str] = field(default_factory=list)
    encounters: List[EncounterRecord] = field(default_factory=list)


@dataclass(frozen=True)
class EchoRecord:
    id: int
    echo: FrozenEcho
    power_score: int
    favorite: bool = False
    icon: str = "default"


@dataclass(frozen=True)
class EchoExchangeReward:
    essence: int
    shards: int
    relic_rolls: int


class EchoPool:
    def __init__(self, capacity: int = 100, max_favorites: Optional[int] = None):
        self.capacity = max(1, capacity)
        requested_max_favorites = self.capacity - 1 if max_favorites is None else max(0, max_favorites)
        self.max_favorites = min(self.capacity - 1, requested_max_favorites)
        self.records: List[EchoRecord] = []
        self._next_id = 1

    def __len__(self) -> int:
        return len(self.records)

    @property
    def is_full(self) -> bool:
        return len(self.records) >= self.capacity

    @property
    def favorite_count(self) -> int:
        return sum(1 for record in self.records if record.favorite)

    @staticmethod
    def power_score(echo: FrozenEcho) -> int:
        stat_score = sum(value.magnitude * 10_000 + value.mantissa for value in echo.stats.values())
        skill_score = len(echo.skills) * 250
        trait_score = len(echo.traits) * 500
        lineage_score = echo.lineage_depth * 100
        instability_cost = echo.instability * 50
        return max(0, stat_score + skill_score + trait_score + lineage_score - instability_cost)

    def bank_echo(self, echo: FrozenEcho, icon: str = "default", favorite: bool = False) -> EchoRecord:
        if self.is_full:
            raise ValueError("echo pool is full")
        if favorite and self.favorite_count >= self.max_favorites:
            raise ValueError("favorite limit reached")
        record = EchoRecord(self._next_id, echo, self.power_score(echo), favorite, icon)
        self._next_id += 1
        self.records.append(record)
        return record

    def get_record(self, record_id: int) -> Optional[EchoRecord]:
        for record in self.records:
            if record.id == record_id:
                return record
        return None

    def update_record(self, record_id: int, *, favorite: Optional[bool] = None, icon: Optional[str] = None) -> EchoRecord:
        for index, record in enumerate(self.records):
            if record.id == record_id:
                if favorite and not record.favorite and self.favorite_count >= self.max_favorites:
                    raise ValueError("favorite limit reached")
                updated = EchoRecord(
                    record.id,
                    record.echo,
                    record.power_score,
                    record.favorite if favorite is None else favorite,
                    record.icon if icon is None else icon,
                )
                self.records[index] = updated
                return updated
        raise KeyError(record_id)

    def delete_echo(self, record_id: int, allow_favorite: bool = False) -> EchoRecord:
        for index, record in enumerate(self.records):
            if record.id == record_id:
                if record.favorite and not allow_favorite:
                    raise ValueError("favorite echoes must be unfavorited before deletion")
                return self.records.pop(index)
        raise KeyError(record_id)

    def exchange_echo(self, record_id: int, event_multiplier: int = 1, allow_favorite: bool = False) -> EchoExchangeReward:
        record = self.delete_echo(record_id, allow_favorite)
        multiplier = max(1, event_multiplier)
        return EchoExchangeReward(
            essence=max(1, record.power_score // 100) * multiplier,
            shards=(10 + record.echo.lineage_depth * 5) * multiplier,
            relic_rolls=(1 + len(record.echo.skills) // 2) * multiplier,
        )

    def exchange_event(self, record_ids: List[int], event_multiplier: int = 1, allow_favorite: bool = False) -> EchoExchangeReward:
        if len(record_ids) != len(set(record_ids)):
            raise ValueError("duplicate echo in exchange selection")
        for record_id in record_ids:
            record = self.get_record(record_id)
            if record is None:
                raise KeyError(record_id)
            if record.favorite and not allow_favorite:
                raise ValueError("favorite echoes must be unfavorited before exchange")
        total = EchoExchangeReward(0, 0, 0)
        for record_id in record_ids:
            reward = self.exchange_echo(record_id, event_multiplier, allow_favorite)
            total = EchoExchangeReward(
                essence=total.essence + reward.essence,
                shards=total.shards + reward.shards,
                relic_rolls=total.relic_rolls + reward.relic_rolls,
            )
        return total

    def sorted_records(self, by: str = "power", descending: bool = True) -> List[EchoRecord]:
        sorters = {
            "power": lambda record: (record.power_score, record.id),
            "icon": lambda record: (record.icon, record.power_score, record.id),
            "favorite": lambda record: (record.favorite, record.power_score, record.id),
            "source": lambda record: (record.echo.source_character_id, record.power_score, record.id),
            "lineage": lambda record: (record.echo.lineage_depth, record.power_score, record.id),
        }
        return sorted(self.records, key=sorters.get(by, sorters["power"]), reverse=descending)

    def top(self, limit: int = 5) -> List[EchoRecord]:
        return self.sorted_records("power")[: max(0, limit)]

    def best_parents(self, source_character_id: Optional[str] = None, count: int = 2) -> List[FrozenEcho]:
        matches = (
            record.echo
            for record in self.sorted_records("power")
            if source_character_id is None or record.echo.source_character_id == source_character_id
        )
        return list(matches)[: max(0, count)]


class GachaSystem:
    resonance_nodes = (
        (20, "origin story"),
        (40, "signature skill variant"),
        (80, "alternate portrait"),
        (120, "lineage title"),
    )
    base_rarity_rates = {
        "common": 79.5,
        "rare": 15.0,
        "epic": 4.0,
        "legendary": 1.5,
    }
    banner_tuning = {
        False: {
            "soft_pity_start": 70,
            "hard_pity_target": 90,
            "legendary_shards": 10,
            "non_legendary_shards": 1,
            "soft_pity_increment": 4.5,
        },
        True: {
            "soft_pity_start": 60,
            "hard_pity_target": 80,
            "legendary_shards": 15,
            "non_legendary_shards": 2,
            "soft_pity_increment": 4.5,
        },
    }

    def __init__(self, characters: Dict[str, CharacterDef], seed: int = 1):
        self.characters = characters
        self.rng = Random(seed)
        self.banners = {cid: BannerState(cid) for cid in characters}

    @classmethod
    def rarity_rates(cls) -> Dict[str, float]:
        return dict(cls.base_rarity_rates)

    @classmethod
    def pity_tuning(cls, featured: bool = False) -> Dict[str, float]:
        return dict(cls.banner_tuning[featured])

    @classmethod
    def resonance_track(cls) -> List[Dict[str, object]]:
        return [
            {"level": index, "cost": cost, "node": node}
            for index, (cost, node) in enumerate(cls.resonance_nodes, start=1)
        ]

    def resonance_preview(self, character_id: str) -> List[Dict[str, object]]:
        banner = self.banners[character_id]
        return [
            {
                "level": entry["level"],
                "cost": entry["cost"],
                "node": entry["node"],
                "unlocked": entry["level"] <= banner.resonance_level,
                "affordable": entry["level"] == banner.resonance_level + 1 and banner.shards >= entry["cost"],
            }
            for entry in self.resonance_track()
        ]

    def next_resonance_cost(self, character_id: str) -> Optional[int]:
        banner = self.banners[character_id]
        if banner.resonance_level >= len(self.resonance_nodes):
            return None
        return self.resonance_nodes[banner.resonance_level][0]

    def upgrade_resonance(self, character_id: str) -> ResonanceUpgrade:
        banner = self.banners[character_id]
        if banner.resonance_level >= len(self.resonance_nodes):
            raise ValueError("resonance track complete")
        cost, node = self.resonance_nodes[banner.resonance_level]
        if banner.shards < cost:
            raise ValueError("not enough shards")
        banner.shards -= cost
        banner.resonance_level += 1
        return ResonanceUpgrade(character_id, banner.resonance_level, node, cost, banner.shards)

    def pull(self, banner_character_id: str, featured: bool = False) -> PullResult:
        banner = self.banners[banner_character_id]
        tuning = self.pity_tuning(featured)
        banner.pulls_since_legendary += 1
        soft_pity_start = tuning["soft_pity_start"]
        hard_pity_target = tuning["hard_pity_target"]
        legendary_shards = tuning["legendary_shards"]
        non_legendary_shards = tuning["non_legendary_shards"]
        legendary_chance = self.base_rarity_rates["legendary"]
        if banner.pulls_since_legendary >= soft_pity_start:
            legendary_chance += (banner.pulls_since_legendary - soft_pity_start + 1) * tuning["soft_pity_increment"]
        hard_pity = banner.pulls_since_legendary >= hard_pity_target
        epic_threshold = self.base_rarity_rates["legendary"] + self.base_rarity_rates["epic"]
        rare_threshold = epic_threshold + self.base_rarity_rates["rare"]
        roll = self.rng.uniform(0, 100)
        if hard_pity or roll <= legendary_chance:
            banner.pulls_since_legendary = 0
            banner.shards += legendary_shards
            return PullResult(Rarity.LEGENDARY, banner_character_id, legendary_shards, True)
        if roll <= epic_threshold:
            rarity = Rarity.EPIC
        elif roll <= rare_threshold:
            rarity = Rarity.RARE
        else:
            rarity = Rarity.COMMON
        banner.shards += non_legendary_shards
        return PullResult(rarity, banner_character_id, non_legendary_shards, False)

    def pull_batch(self, banner_character_id: str, count: int = 10, featured: bool = False) -> List[PullResult]:
        return [self.pull(banner_character_id, featured) for _ in range(max(0, count))]

    def featured_banners_for_week(self, week: int, slots_per_week: int = 3) -> List[str]:
        ids = sorted(self.characters)
        if not ids or slots_per_week <= 0:
            return []
        start = ((max(1, week) - 1) * slots_per_week) % len(ids)
        return [ids[(start + index) % len(ids)] for index in range(min(slots_per_week, len(ids)))]

    def featured_schedule(self, weeks: int = 52, slots_per_week: int = 3) -> List[List[str]]:
        return [self.featured_banners_for_week(week, slots_per_week) for week in range(1, max(0, weeks) + 1)]

    def featured_coverage(self, weeks: int = 52, slots_per_week: int = 3) -> List[str]:
        seen = set()
        for banners in self.featured_schedule(weeks, slots_per_week):
            seen.update(banners)
        return sorted(seen)

    def annual_featured_counts(self, weeks: int = 52, slots_per_week: int = 3) -> Dict[str, int]:
        counts = {character_id: 0 for character_id in self.characters}
        for week in range(1, max(0, weeks) + 1):
            for character_id in self.featured_banners_for_week(week, slots_per_week):
                counts[character_id] += 1
        return counts

    def missing_annual_featured_banners(self, weeks: int = 52, slots_per_week: int = 3) -> List[str]:
        counts = self.annual_featured_counts(weeks, slots_per_week)
        return sorted(character_id for character_id, count in counts.items() if count == 0)


class RelicForge:
    relic_rarities = (
        (60, Rarity.COMMON, 8),
        (85, Rarity.RARE, 15),
        (97, Rarity.EPIC, 25),
        (100, Rarity.LEGENDARY, 40),
    )
    relic_stats = ("hp", "atk", "def", "spd")

    def __init__(self, seed: int = 4):
        self.rng = Random(seed)
        self._next_id = 1

    def roll_relic(self) -> Relic:
        roll = self.rng.uniform(0, 100)
        rarity, bonus = Rarity.COMMON, 8
        for threshold, relic_rarity, relic_bonus in self.relic_rarities:
            if roll <= threshold:
                rarity, bonus = relic_rarity, relic_bonus
                break
        stat = self.relic_stats[self.rng.randrange(len(self.relic_stats))]
        relic = Relic(self._next_id, f"{rarity.value.title()} {stat.upper()} Sigil", rarity, stat, bonus)
        self._next_id += 1
        return relic

    def forge(self, relic_rolls: int) -> List[Relic]:
        return [self.roll_relic() for _ in range(max(0, relic_rolls))]

    @staticmethod
    def apply_relics(stats: Stats, relics: List[Relic]) -> Stats:
        boosted = dict(stats)
        for relic in relics:
            current = boosted.get(relic.stat, BigStat(0))
            boosted[relic.stat] = current.scale(100 + relic.bonus_percent)
        return boosted


class TrainingSimulator:
    route_growth = {
        "balanced": (112, 4),
        "boss_rush": (118, 5),
        "skill_hunt": (108, 3),
        "deep_scaling": (125, 8),
    }
    max_parents = 2

    def __init__(self, seed: int = 2, checkpoint_interval: int = 4):
        self.rng = Random(seed)
        self.checkpoint_interval = max(1, checkpoint_interval)

    @classmethod
    def available_routes(cls) -> Tuple[str, ...]:
        return tuple(cls.route_growth)

    @classmethod
    def route_tuning(cls, route: str) -> Dict[str, int]:
        if route not in cls.route_growth:
            raise ValueError(
                f"unknown training route {route!r}; choose from {', '.join(cls.available_routes())}"
            )
        growth_percent, magnitude_interval = cls.route_growth[route]
        return {"growth_percent": growth_percent, "magnitude_interval": magnitude_interval}

    def checkpoint_reward(self, tier: int, floor: int) -> CheckpointReward:
        return CheckpointReward(
            floor=floor,
            tier=tier,
            shards=15 * (2**(tier - 1)),
            relic_rolls=tier,
            echo_quality_bonus=20 * tier,
        )

    @staticmethod
    def encounter_kind(floor: int, route: str = "balanced") -> str:
        if floor % 4 == 0:
            return "boss"
        route_encounters = {
            "balanced": ("combat", "event", "rest", "elite"),
            "boss_rush": ("combat", "elite", "rest", "elite"),
            "skill_hunt": ("event", "combat", "rest", "shrine"),
            "deep_scaling": ("combat", "shrine", "rest", "elite"),
        }.get(route, ("combat", "event", "rest", "elite"))
        return route_encounters[(floor - 1) % len(route_encounters)]

    def start_stats(
        self, character: CharacterDef, parents: Optional[Sequence[FrozenEcho]] = None
    ) -> Tuple[Stats, int, int]:
        parents = tuple(parents) if parents else ()
        if len(parents) > self.max_parents:
            raise ValueError(f"at most {self.max_parents} parents may be inherited, got {len(parents)}")
        stats = dict(character.base_stats)
        lineage_depth = max((parent.lineage_depth for parent in parents), default=-1) + 1
        instability = 0
        for parent in parents:
            depth_factor = max(35, 100 - parent.lineage_depth * 8)
            for stat_name, parent_value in parent.stats.items():
                inherited = parent_value.scale(25 * depth_factor, 10000)
                stats[stat_name] = stats.get(stat_name, BigStat(0)).add(inherited)
                instability += max(0, inherited.magnitude - character.base_stats.get(stat_name, BigStat(1)).magnitude)
        return stats, lineage_depth, instability

    def run(
        self, character: CharacterDef, route: str = "balanced", parents: Optional[Sequence[FrozenEcho]] = None
    ) -> RunResult:
        tuning = self.route_tuning(route)
        stats, lineage_depth, instability = self.start_stats(character, parents)
        log: List[str] = []
        growth_percent = tuning["growth_percent"]
        magnitude_interval = tuning["magnitude_interval"]
        floors_cleared = 0
        rewards = RunRewards()
        encounters: List[EncounterRecord] = []
        for floor in range(1, 13):
            power = sum(value.mantissa + value.magnitude * 1000 for value in stats.values())
            difficulty = 120 + floor * floor * 65 + instability * 40
            kind = self.encounter_kind(floor, route)
            if power < difficulty and self.rng.random() < 0.45:
                encounters.append(EncounterRecord(floor, kind, power, difficulty, False))
                log.append(f"failed {kind} floor {floor} at power {power} vs difficulty {difficulty}")
                break
            encounters.append(EncounterRecord(floor, kind, power, difficulty, True))
            floors_cleared = floor
            for stat_name, value in list(stats.items()):
                stats[stat_name] = value.scale(growth_percent)
                if floor % magnitude_interval == 0:
                    stats[stat_name] = BigStat(stats[stat_name].mantissa, stats[stat_name].magnitude + 1).normalized()
            if floor % 4 == 0:
                log.append(f"boss gate {floor} cleared")
            if floor % self.checkpoint_interval == 0:
                tier = floor // self.checkpoint_interval
                reward = self.checkpoint_reward(tier, floor)
                rewards.checkpoints.append(reward)
                rewards.banked_shards += reward.shards
                rewards.relic_rolls += reward.relic_rolls
                rewards.highest_checkpoint_floor = floor
                rewards.echo_quality_percent += reward.echo_quality_bonus
                dividend = instability * 5 * tier
                rewards.instability_dividend_shards += dividend
                rewards.banked_shards += dividend
                log.append(
                    f"checkpoint tier {tier} banked at floor {floor}: "
                    f"+{reward.shards} shards, +{reward.relic_rolls} relic rolls, "
                    f"+{dividend} instability dividend, "
                    f"echo quality {rewards.echo_quality_percent}%"
                )
        victory = floors_cleared == 12
        echo_stats = {name: value.scale(rewards.echo_quality_percent) for name, value in stats.items()}
        echo = FrozenEcho(
            source_character_id=character.id,
            stats=echo_stats,
            skills=character.skills[:3],
            traits=character.traits[:2],
            lineage_depth=lineage_depth,
            instability=instability,
        )
        return RunResult(floors_cleared, victory, echo, rewards, log, encounters)


def sample_characters() -> Dict[str, CharacterDef]:
    return {
        "iron_vow": CharacterDef(
            "iron_vow",
            "Astra, Iron Vow",
            Rarity.LEGENDARY,
            "guardian",
            {"hp": BigStat(900), "atk": BigStat(90), "def": BigStat(140), "spd": BigStat(45)},
            ("Aegis Break", "Oath Wall", "Counterflare"),
            ("armor", "counter"),
        ),
        "star_witch": CharacterDef(
            "star_witch",
            "Mira, Star Witch",
            Rarity.LEGENDARY,
            "caster",
            {"hp": BigStat(430), "atk": BigStat(180), "def": BigStat(55), "spd": BigStat(80)},
            ("Nova Hex", "Meteor Seed", "Astral Refund"),
            ("magic", "scaling"),
        ),
        "rat_squire": CharacterDef(
            "rat_squire",
            "Pip, Rat Squire",
            Rarity.RARE,
            "fighter",
            {"hp": BigStat(520), "atk": BigStat(95), "def": BigStat(80), "spd": BigStat(100)},
            ("Skitter Strike", "Tiny Guard"),
            ("beast", "underdog"),
        ),
    }


def demo() -> Dict[str, object]:
    characters = sample_characters()
    gacha = GachaSystem(characters)
    simulator = TrainingSimulator()
    pulls = [gacha.pull("star_witch") for _ in range(10)]
    first = simulator.run(characters["star_witch"], "deep_scaling")
    echo_pool = EchoPool(capacity=5)
    first_record = echo_pool.bank_echo(first.echo)
    second = simulator.run(characters["star_witch"], "deep_scaling", echo_pool.best_parents())
    second_record = echo_pool.bank_echo(second.echo)
    third = simulator.run(characters["iron_vow"], "deep_scaling", echo_pool.best_parents())
    third_record = echo_pool.bank_echo(third.echo)
    forge = RelicForge()
    relics = forge.forge(third.rewards.relic_rolls)
    forged_stats = RelicForge.apply_relics(third.echo.stats, relics)
    print("featured_week_1", gacha.featured_banners_for_week(1))
    print("pulls", [(pull.rarity.value, pull.shards_gained) for pull in pulls])
    print("run_1", first.floors_cleared, first.victory, {k: str(v) for k, v in first.echo.stats.items()})
    print("run_1_rewards", first.rewards.banked_shards, first.rewards.relic_rolls,
          f"echo_quality={first.rewards.echo_quality_percent}%",
          f"highest_checkpoint={first.rewards.highest_checkpoint_floor}")
    print("run_2", second.floors_cleared, second.victory, {k: str(v) for k, v in second.echo.stats.items()})
    print("run_2_rewards", second.rewards.banked_shards, second.rewards.relic_rolls,
          f"echo_quality={second.rewards.echo_quality_percent}%",
          f"highest_checkpoint={second.rewards.highest_checkpoint_floor}")
    print("run_3_two_parent", third.floors_cleared, third.victory, third.echo.lineage_depth,
          {k: str(v) for k, v in third.echo.stats.items()})
    print("run_3_rewards", third.rewards.banked_shards, third.rewards.relic_rolls,
          f"echo_quality={third.rewards.echo_quality_percent}%",
          f"highest_checkpoint={third.rewards.highest_checkpoint_floor}")
    print("echo_pool", [(record.id, record.power_score) for record in echo_pool.top()],
          f"banked={[first_record.id, second_record.id, third_record.id]}")
    print("relics", [(relic.rarity.value, relic.stat, relic.bonus_percent) for relic in relics])
    print("forged_stats", {k: str(v) for k, v in forged_stats.items()})
    return {
        "pulls": pulls,
        "first": first,
        "second": second,
        "third": third,
        "echo_pool": echo_pool,
        "banked_records": [first_record, second_record, third_record],
        "relics": relics,
        "forged_stats": forged_stats,
    }


if __name__ == "__main__":
    demo()
