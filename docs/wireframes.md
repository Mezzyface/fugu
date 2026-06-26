# Fugu — screen wireframes (UI guide)

Transcribed from `docs/wireframes/Fugu-Wireframes.html` (open it in a browser to see the
visual canvas). This is the authoritative screen map. Each screen binds to logic in
`prototype/game.py` (the Python prototype) — the Godot screens implement these flows against
ported game logic. Visuals follow [`docs/art_direction.md`](art_direction.md) (Tiny Swords
sprites, Isometric terrain, honeyblot_caps/HoneyPigeon fonts, Wada Sanzo palette).

Legend: sequential flow · inheritance feedback · UI region/placeholder · art slot.

## Screen map (navigation)

`Home/Hub` → Banner Select → Banner/Pull → (obtain char) → Run Setup → Run In Progress →
Run Results → Echo Pool ⇄ Exchange Event; Run Results → Relic Forge; Hub → Character Collection.
Echo Pool `best_parents()` → ≤2 parents power the next run.

## 01 · Home / Hub  — *entry · navigation root*
- FUGU logo; currency totals: ◆ shards · ✦ essence · ⬡ relic rolls.
- "★ Featured this week — Week N / 52 · 3 banners" (`GachaSystem.featured_banners_for_week(week)`).
- Nav buttons → Banner, New Run, Echo Pool, Relic Forge, Exchange, Settings.
- Data: `GameSession` (totals); resolve current week in 52-slot cycle. Every screen reachable from hub.

## 02 · Banner Select — *annual rotation · gallery*
- "Week N / 52 — featured group"; character portraits: Star Witch (★ Featured), Iron Vow, Ashling,
  Tideborn, Gravewarden, + more; permanent vs featured.
- Data: `characters{}`, `GachaSystem.featured_schedule(52,3)`, `annual_featured_counts()`.
- Rule: every character featured ≥1×/yr (`missing_annual_featured_banners()` empty); **no FOMO copy**.

## 03 · Banner / Pull — *gacha pull · pity · resonance*
- Character art (e.g. STAR WITCH · LEGENDARY); pity bar (`BannerState.pulls_since_legendary /
  hard_pity_target`), e.g. pity 49/90 (soft 60 · hard 90 · featured 80).
- Resonance: 20/40/80/120 shards → ◇◇◇◇; latest result → rarity badge · pity-reset flash · +shards.
- Buttons: Pull ×1 (`pull()`), Pull ×10 (`pull_batch()`). `upgrade_resonance()` spends shards, never base stats.
- Base rates 79.5 / 15 / 4 / 1.5 %. Data: `BannerState`, `PullResult`, `GachaSystem.pull/pull_batch`.

## 04 · Run Setup — *character · parents · route*
- BASE CHARACTER (`CharacterDef`); PARENT 1 / PARENT 2 (drag echo, optional) — `FrozenEcho`.
- ROUTE (`available_routes()`): Balanced, Boss Rush, Skill Hunt, Deep Scaling.
- Projected start stats (`start_stats()`), instability ⚠. ▶ Start Run.
- Data: `best_parents(src, 2)` (max_parents=2), `TrainingSimulator.run()` preview.

## 05 · Run In Progress — *12-floor map · encounters · checkpoints*
- Boss gates at floors 4/8/12 = checkpoints (`checkpoint_interval=4`); elite floors.
- e.g. "Floor 9 · ELITE — power 4.2e3 vs difficulty 3.8e3"; "✓ checkpoint banked — F8 · +30◆ +2⬡ +40% echo".
- Dividend ⚠ instability×5×tier. Deterministic per route · step-through playback.
- Data: `RunResult.encounters[]`, `EncounterRecord`, `RunRewards.checkpoints[]`, `CheckpointReward`.
- Each floor drills into ONE Encounter Moment (below), selected by
  `TrainingSimulator.encounter_kind(floor, route)`.

## 06 · Run Results — *frozen echo · always-echo*
- VICTORY (cleared 12/12) or DEFEAT (floor N). FROZEN ECHO · source char.
- Stats HP/ATK/DEF/SPD (display = mantissa·10^magnitude); skills ≤3 · traits ≤2; lineage depth · instability ⚠.
- Rewards: +◆ banked shards, +⬡ relic rolls, echo quality %, +◆ dividend.
- Buttons: ⬇ Bank Echo (`EchoPool.bank_echo(echo)`), ⬡ Forge Relics (`RelicForge.forge(relic_rolls)`).

## 07 · Echo Pool — *inheritance inventory*
- Sortable list (power · icon · favorite · source · lineage), e.g. "#42 star_witch · pwr 9.4e6 · lin 4".
- Actions: ⇄ exchange · 🗑 delete · ♥ favorite (protected).
- Data: `EchoPool`, `EchoRecord`, `sorted_records(by)`, `update_record()`, `delete_echo()`, `exchange_echo()`.

## 08 · Exchange Event — *timed · echo sink (batch)*
- e.g. "Resonant Tide — ×3 multiplier · 2d left"; multi-select echoes (favorites locked).
- "4 selected → +480✦ +120◆ +9⬡"; Confirm.
- Data: `EchoExchangeReward`, `event_multiplier`, `EchoPool.exchange_event(record_ids, event_multiplier)`.
  Favorites excluded unless `allow_favorite`; multiplier on aggregate; respects ≥1-removable rule.

## 09 · Relic Forge — *relic-roll sink*
- "⬡ relic rolls available — N"; Forge; results e.g. Bulwark Shard (COMMON +8% DEF), Ember Fang (EPIC +25% ATK).
- Odds C 60/8% · R 25/15% · E 12/25% · L 3/40%. Apply → echo.
- Data: `Relic(rarity, stat, bonus_percent)`, `roll_relic()`, `forge(n)`, `apply_relics(stats, relics)`.

## 10 · Character Collection — *roster · resonance*
- filter ▾ role · sort ▾ rarity; "owned 7/24"; e.g. Star Witch ◇◇◇◆, Iron Vow ◇◇◆◆; 🔒 locked.
- Data: `BannerState.resonance_level` per owned char; `CharacterDef.rarity`.
- Open detail · jump to banner (03) · select for run (04). Pulled chars land here.

## Encounter Moments (screen 05 drills into one per floor)
Selected deterministically by `TrainingSimulator.encounter_kind(floor, route)`:
- **⚔ Combat** (`kind="combat"`) — enemy unit(s) · **Tiny Swords**; power vs diff; clear → XP · mantissa stat growth · chance of run relic. `EncounterRecord.cleared` if power ≥ difficulty.
- **📖 Event** (`kind="event"`) — narrative prompt, Option A/B → relic / skill mutation / risk; auto-cleared; logged to `RunResult.log`.
- **🗡 Elite** (`kind="elite"`) — elite enemy pack; higher difficulty; richer relic + mutation rolls.
- **👑 Boss Gate** (`kind="boss"`, F4/8/12) — boss; clear → checkpoint banked instantly; `15·2^(t−1)◆ · tier ⬡ · +20%·t echo · instability dividend`; kept even if run later fails.
- **🕯 Shrine** (`kind="shrine"`) — pick a skill mutation / blessing (run-scoped); auto-cleared; logged.
- **⛺ Rest** (`kind="rest"`) — campfire safe floor: Heal / Upgrade relic; no combat.

## Build notes
- Screens are built in Godot under `game/scenes/<screen>.tscn` + scripts; wire to game logic
  ported from `prototype/game.py` (don't reinvent the math — port `GachaSystem`, `TrainingSimulator`,
  `EchoPool`, `RelicForge`, etc.).
- Large numbers display as mantissa·10^magnitude (e.g. `8.4e4`), not raw integers.
- Apply the project Theme (fonts + palette) to every screen; combat uses Tiny Swords sprites,
  maps use Isometric terrain, missing art falls back to Prototype Textures.
