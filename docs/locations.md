# Locations along the road – There and Back Again

This document lists every place on the route as the game builds it (`hobbit/journey.py`).
For each one it gives:

- **Game**: what the game draws now.
- **Book**: how *The Hobbit* describes the place.
- **Weather**: how the place should look in each weather the region can roll.
- **Time of day**: how it should look at dawn, by day, at dusk and at night.

Lines marked **Idea** are suggestions, not current behaviour.
Distances are route km from Bag End; the return trip runs the same km backwards.

## How weather and light work now

Use this as the baseline for the per-location notes below.

**Time of day** (`palette.py`, `_KEYS`). The light is a palette multiplier that steps every 10 game minutes:

| Game hour | Phase | Sky (top → horizon) | Land |
| --- | --- | --- | --- |
| 21:00 – 04:30 | night | near-black navy → dark blue | dimmed to about a third, tinted blue |
| 04:30 – 07:30 | dawn | navy → orange glow at 06:00 → day blue | warms up, pinkish at 06:00 |
| 07:30 – 17:30 | day | deep blue → pale blue | full colour |
| 17:30 – 21:00 | dusk | blue → purple and red-orange at 19:20 → night | orange-red, then dims |

- The sun crosses the sky from 05:30 to 19:30; the moon (a crescent) shows the rest of the time.
- Stars appear from 19:00 to 06:00. They are hidden in proportion to overcast.
- Lit windows (`WINDOW`) are dark glass by day and fade to warm yellow as night falls.
  Hobbit holes, the Green Dragon, Elrond's houses, Beorn's hall and the Lake-town stilt houses have them.
- Torches (`FLAME`) are emissive and flicker. They are never dimmed by night or gloom.
- Eyes (`EYES`) are dull dark olive by day and glow yellow-green once night is past halfway.
  The Mirkwood eyes, the spiders' eyes and Gollum's eyes use this colour.
- Underground (`cave` in Goblin-town) the light is fixed: the tunnel looks the same at noon and at midnight, and eyes always glow.
- One in-game day lasts `day_length_minutes` real minutes (24 by default).

**Weather** (`game.py`) is re-rolled every 6 game hours from the region's weights:

| Weather | Overcast | What you see |
| --- | --- | --- |
| clear | 0.0 | 3 clouds |
| cloudy | 0.45 | 6 clouds, greyer sky, land a little dimmer |
| rain | 0.8 | 8 clouds, grey sky, 90 blue rain streaks slanting left |
| snow | 0.7 | 8 clouds, 110 drifting snow flecks |
| storm | 1.0 | 8 clouds, 150 rain streaks, lightning bolts with a full-screen white flash about every 9 s |

- Unless a region says otherwise, weather is clear 70 %, cloudy 20 %, rain 10 %.
- The book fixes the weather in two places, on the way there only (`FORCED_WEATHER`):
  rain at km 465–471 around the Last Bridge, and the storm at km 795–800 below the High Pass.
- On the way back, the Desolation and Erebor can also roll snow (winter after the battle).
- A change of weather is eased in: the sky moves to the new overcast over about 20 seconds,
  rain or snow thickens as the clouds come in, and lightning starts once the storm clouds are in.
- In Goblin-town nothing falls.
- In Mirkwood only a third of the rain gets through the canopy.

**Gloom** darkens the land and turns the sky green-black.
It is 0.55 in Goblin-town, 0.5 in Mirkwood and 0.3 at the Elvenking's halls, blended across region borders.
A black leaf canopy closes over the sky as the (blended) gloom rises from 0.1 to 0.3, so it lifts gradually when you leave the forest.

**Transitions between regions.** Within 300 m of a border, the two regions' background layers are dithered together (an ordered 4×4 pattern),
and both regions' haze colours are in the palette at once (alternate slot sets by region parity).
Ground colours, hills, curves, path width and gloom are blended over the same distance.

**Seasons** are not modelled.
In the book the Company leaves in spring, crosses the mountains in summer, and reaches Lake-town and the Mountain in autumn.
The Battle of Five Armies is in winter.
Bilbo spends Yule at Beorn's, crosses the mountains in spring and is home in early summer.
**Idea:** tint the ground and change the weather weights by season, using total distance or journey leg.

## Trail and horizon in the game now

**Trail.** The path is a striped strip; its half-width per region is in `PATH_WIDTH` (`journey.py`):

| Path half-width | Regions |
| --- | --- |
| 1.2–1.3 m (a road) | Hobbiton, the Shire, the East Road, the Lake-town causeway, Erebor |
| 0.9–1.05 m (a track) | the Lone-lands, Rivendell, the Vale of Anduin, Beorn's lands, the Elvenking's halls, the Forest River, the River Running, the Desolation |
| 0.75–0.85 m (single file) | the Trollshaws, the Misty Mountains, Goblin-town, the Eastern Slopes, Mirkwood |

- Bridges are grey stone, the causeway is planks and fords are animated water.
- Hills and curves grow with the region's `hills` and `curves` values; the Misty Mountains are the steepest (12 m) and twistiest.
- **Idea:** surface types the book describes but the game lacks: mud in rain, loose scree, white marker stones and steps cut in rock.

**Horizon.** Each region has a far layer (`bg_far`) and a near layer (`bg_near`): hills, forest, mountains, cliffs, a low far mountain or flat land.
- A region's `back` overrides give the horizon (and weather) on the way back, so each direction shows what lies ahead.
  For example, Beorn's lands show the black line of Mirkwood on the way east and the snowy Misty Mountains on the way west.
- The Lonely Mountain rises ahead from km 1250 on the way there, in its own colour, and is never drawn on the way back.
- Bilbo's own Hill rises ahead over the last 6 km on the way back.

## Overview

| km | Place | Kind | Region |
| --- | --- | --- | --- |
| 0 | Bag End | landmark, set piece | Hobbiton (0–2) |
| 2 | The Green Dragon, Bywater | landmark, set piece | Hobbiton / The Shire (2–70) |
| 2–70 | The Shire | region | |
| 70 | The Brandywine Bridge | landmark, stone bridge | The Shire → The East Road |
| 70–220 | The East Road | region | |
| 220–470 | The Lone-lands | region | |
| 300 | Weathertop (hill ruin) | landmark, set piece | The Lone-lands |
| 470 | The Last Bridge | landmark, stone bridge | The Lone-lands → The Trollshaws |
| 470–725 | The Trollshaws | region | |
| 600 | The Stone Trolls | landmark, 3 trolls | The Trollshaws |
| 720 | The Ford of Bruinen | landmark, ford | The Trollshaws |
| 725–745 | Rivendell Vale | region (gorge edge) | |
| 739.8–740.1 | Rivendell, the Last Homely House | landmark, 5 elf houses | Rivendell Vale |
| 745–800 | The Misty Mountains | region | |
| 465–471 | Rain | forced rain (way there) | The Lone-lands / The Trollshaws |
| 795–800 | Thunderstorm | forced storm (way there) | The Misty Mountains |
| 799 | The High Pass | landmark | The Misty Mountains |
| 800–812 | Goblin-town | region (tunnel) | |
| 806 | Gollum's lake | landmark | Goblin-town |
| 812–835 | The Eastern Slopes | region | |
| 813–845 | Eagles circling | sky | Eastern Slopes / Vale of Anduin |
| 825 | The Eagles' Eyrie | landmark | The Eastern Slopes |
| 835–875 | The Vale of Anduin | region | |
| 866–874 | The Great River (right side) | water | The Vale of Anduin |
| 870 | The Carrock | landmark, set piece | The Vale of Anduin |
| 875–940 | Beorn's lands | region | |
| 887–893 | Beehives | 14 set pieces | Beorn's lands |
| 890 | Beorn's house | landmark, hall | Beorn's lands |
| 940 | The Forest Gate | landmark, gate, forest face | Beorn's lands → Mirkwood |
| 940–1245 | Mirkwood | region | |
| 1050 | The Enchanted River | landmark, ford | Mirkwood |
| 1148–1152 | The Spiders' nests | landmark, 60 webs and spiders | Mirkwood |
| 1245–1250 | The Elvenking's halls | region, landmark, gate | |
| 1250–1400 | The Forest River | region (river on the right) | |
| 1400–1420 | The Long Lake | region, plank causeway | |
| 1412–1418 | Lake-town, Esgaroth | landmark, 18 stilt houses | The Long Lake |
| 1420–1470 | The River Running | region (river on the left) | |
| 1470–1527 | The Desolation of Smaug | region, Smaug at night, smoke by day | |
| 1527–1530 | Erebor, the Lonely Mountain | region, landmark, front gate | |

From about km 1250 (280 km out) Erebor shows on the horizon on the way there.
It grows until km 1500, where it switches to the detailed close-up.

---

## Bag End – km 0

**Game:** The Bag End sprite with a round green door, at the very start of the road.
Gandalf walks with Bilbo; the dwarves join at km 2.
The sign, quote: *In a hole in the ground there lived a hobbit.*

**Book:** A hobbit-hole, "and that means comfort", dug into the Hill.
It has a perfectly round green door with a shiny yellow brass knob in the exact middle.
A tunnel-like hall with panelled walls and tiled floors leads off it.
Deep round windows on the left side look over the garden and the meadows sloping down to the Water.
It is a tidy, prosperous place with no adventures.
Gandalf scratches a secret mark on the door.
The Company leaves on a spring morning, after Bilbo wakes late to a messy kitchen.

**Trail (book):** No trail yet: a lane runs down the Hill, past the mill and across the Water, to Bywater.

**Horizon on the way there:** Bilbo hardly looks; he runs. Ahead lie the roofs of Hobbiton and Bywater, the Water and the Pool, and gentle green country.

**Horizon on the way back:** The book's homecoming image. Coming over a rise, Bilbo sees his own Hill in the distance and stops to say "Roads go ever ever on".
The Hill should rise ahead for the last few km, with the round windows of Bag End catching the light.

**Horizon in the game:** soft green hills in both directions.

**Weather**
- Clear: the classic picture; the green door bright, the flowers on the hill in colour, smoke from the chimney.
- Cloudy: soft light, colours muted, still homely.
- Rain: the green door wet and dark, puddles on the path.
  **Idea:** lit windows even by day, since in rain the hole looks cosy rather than gloomy.

**Time of day**
- Dawn: low golden light on the Hill. This is when Bilbo would be having breakfast; the windows are just lit.
- Day: full colour.
- Dusk: windows glowing, long shadows.
  On the return the book has Bilbo arrive home in early summer to find his own auction under way, so an evening return fits.
- Night: dark hill, yellow round windows, stars over the Hill.

## The Green Dragon, Bywater – km 2

**Game:** The Green Dragon inn at the left of the road, with lit windows.
Here the dwarves join the walk.
Quote: *Bilbo ran all the way – without a pocket-handkerchief.*

**Book:** Bilbo races to the Green Dragon Inn at Bywater to meet the Company at 11 a.m. sharp, as Gandalf's note says.
He has no hat, no walking-stick, no money and no pocket-handkerchief.
The ponies are loaded at the inn and the Company rides off.

**Trail (book):** The village road at Bywater; at the inn the ponies are loaded and the Company rides off.

**Horizon on the way there:** Village, hedges and fields. The Hill and Bag End are behind.

**Horizon on the way back:** The Hill with Bag End is just ahead, about 2 km away.
**Game:** the Hill rises on the horizon over the last 6 km on the way back, with Bag End's round door and windows (lit at night).

**Weather**
- Clear or cloudy: busy mid-morning village; the Pool of Bywater could shine beside the road.
- Rain: as above but drab; the inn sign swings.

**Time of day**
- Day, around 11:00, is the canonical moment.
- Dusk and night: inn windows bright yellow, the busiest look the inn has.

## The Shire – km 2–70

**Game:** Rolling green hills, oaks, bushes, flowers, fences, the odd hobbit hole, milestones.
The road is wide.

**Book:** Tamed, rich farm country.
The Company rides through "hobbit-lands, a wide respectable country inhabited by decent folk, with good roads, an inn or two".
Here and there a dwarf or a farmer is about on business.

**Trail (book):** Good roads through "hobbit-lands, a wide respectable country"; Bilbo rides a pony.

**Horizon on the way there:** Farmland, hedges, woods and low hills, all familiar and tame.

**Horizon on the way back:** The same landscape, now in early summer. Bilbo comes back changed, and the Shire looks small and peaceful.

**Horizon in the game:** green hills in both directions, which fits.

**Weather**
- Clear: summer-green fields, blue sky with three soft clouds.
- Cloudy: the ordinary English-country look.
- Rain: soft, steady drizzle, not threatening.

**Time of day**
- Dawn: mist in the hollows. **Idea:** low ground fog at 04:30–07:30.
- Day: full colour.
- Dusk: golden fields and lit hobbit-hole windows.
- Night: windows dotted along the hills; this is the safest-feeling night on the route.

## The Brandywine Bridge – km 70

**Game:** A stone bridge (grey path, water on both sides, stone parapet posts) where the Shire becomes the East Road.
Quote: *And so they left the Shire behind.*

**Book:** The Hobbit does not name the bridge.
It only says the hobbit-lands gave way to strange country, where people spoke strangely and sang songs Bilbo had never heard.
The Brandywine Bridge belongs to the wider legendarium as the Shire's eastern border on the Great East Road.

**Trail (book):** The road crosses the river by a stone bridge; the book does not describe it.

**Horizon on the way there:** The edge of the Shire. East of the river, the country becomes unknown and strange.

**Horizon on the way back:** Familiar Shire country again past the bridge, the first sight of home.

**Weather**
- Clear: brown-green river under a light grey stone bridge.
- Rain: the water rough and grey, rings on the surface.

**Time of day**
- Dusk and dawn: the river catches the sky colour. **Idea:** blend the water colours toward the horizon colour.
- Night: dark water with a little moonlight.

## The East Road – km 70–220

**Game:** Rougher country: oaks, pines, rocks, tufts and milestones every km.
A forest line stands in the near background.

**Book:** Strange lands beyond the Shire.
The road is still a road, with inns at first, then fewer of them.
Folk become scarce, then unfriendly.

**Trail (book):** Still a road, but the inns grow rarer and poorer and folk speak strangely. Then the road grows worse.

**Horizon on the way there:** Rolling country darkening toward the east, with woods.

**Horizon on the way back:** The country grows tamer and greener toward the Shire.

**Horizon in the game:** hills behind a forest line, which suits both directions.

**Weather**
- Clear: open, still pleasant.
- Cloudy: the land darkens toward the east, as a hint of what is coming.
- Rain: a muddy road. **Idea:** darker path colours in rain.

**Time of day**
- Day: plain.
- Night: no lit windows. The milestones are the only human things.
  **Idea:** an inn with lit windows somewhere around km 100–150, the last inn the Company sees.

## The Lone-lands – km 220–470

**Game:** Yellow-grey grass, rocks, boulders, dead trees, sparse bushes.
The weather is worse here: clear 40 %, cloudy 30 %, rain 30 %.

**Book:** Dreary land with no people and no inns, the road getting worse.
Not far ahead are dismal hills, rising higher and higher, dark with trees.
On some of them stand old castles with an evil look, as if built by wicked people.
It is nearly summer, yet everything seems gloomy, and it rains and rains.

**Trail (book):** A bad road through empty country with no inns; the ponies stumble.
It rains day after day, everything is wet and muddy, and they can't find dry wood for a fire.

**Horizon on the way there:** Dismal hills rising ever higher, dark with trees. On some of them stand old castles with an evil look.
On clear days, near the end, the mountains begin to show far ahead.

**Horizon on the way back:** In the book, Gandalf and Bilbo pass this way in May and early summer, more quickly, on ponies. It is lonely and empty, but no longer dismal.
The Misty Mountains slowly fall away behind.

**Horizon in the game:** yellow-grey hills with small castle silhouettes on the tops (`castle_hills`), in both directions.

**Idea:** a faint grey mountain line on the horizon from about km 400 on the way there.

**Weather**
- Rain should be the normal look here; the book's wettest stretch is the end of the Lone-lands.
- Cloudy: a flat, heavy grey, the evil-looking castles on the skyline.
- Clear: rare. Wide horizon, but it still feels empty.

**Time of day**
- Day: washed-out yellows.
- Dusk: low red light behind the ruins and dead trees, the most "evil castle" look.
- Night: total darkness with no friendly lights.
  This is where the Company see a red light among the trees: the trolls' fire.

## Weathertop – km 300

**Game:** A large hilltop ruin at the left (about 40 m away).
Quote: *Old ruins stood on the hills.*

**Book:** Weathertop (Amon Sûl) is never named in The Hobbit; it belongs to *The Lord of the Rings*.
The book's matching image is the hills with old castles of evil look described above.
Treat this as one of those castles rather than as the named watch-tower.

**Trail (book):** The same bad road. The castle-hills stand close to the road.

**Horizon on the way there:** The ruin looms to the north side of the road, with more castles on the hills ahead.

**Horizon on the way back:** The same ruins, seen from the other side.

**Weather**
- Rain or cloud: the ruin's silhouette against a grey sky, the intended look.
- Clear: stark grey stone over yellow grass.

**Time of day**
- Dusk: the ruin as a black silhouette against red, the strongest picture.
- Night: barely visible against the stars.

## The Last Bridge – km 470

**Game:** A stone bridge into the Trollshaws.
Quote: *It was raining, and had been all day.*

**Book:** The Last Bridge, over the Hoarwell (Mitheithel), is again a Lord of the Rings name.
In The Hobbit, the Company's crossing near here is a river in flood: they pass the night after a pony bolts into the water and most of the food is lost.
The day before the troll camp is the soaking one: wind, rain, a lost fire and failing tempers.

**Trail (book):** The road comes down to a river in flood after the rain. The pony carrying the food bolts into the water, and they lose most of the food.

**Horizon on the way there:** Wooded hills closing in, with steep valleys; dark with rain and growing evening.

**Horizon on the way back:** The open, empty Lone-lands to the west.

**Weather**
- **Game:** rain is forced from km 465 to 471 on the way there, to match the quote.
- Rain: a swollen brown-grey river close below the bridge.

**Time of day**
- Dusk to night is the canonical moment: dark, wet and cold, just before they see the trolls' fire.

## The Trollshaws – km 470–725

**Game:** Dense pines and oaks, rocks, steeper hills and tighter curves.
Weather: clear 40 %, cloudy 30 %, rain 30 %.

**Book:** Hills dark with trees, with paths winding through the wooded valleys.
The trolls have their camp and their cave in this woodland.

**Trail (book):** The Company leaves the road and climbs through trees toward a red light. They go up a slope and down a valley with no path.
After the trolls, they find the trolls' trail to the cave and then return to the road.

**Horizon on the way there:** Only trees, and the red glimmer of the trolls' fire at night.
After the trolls, the book has Bilbo see the mountains looming ahead, and ask if that is *the* Mountain. Gandalf answers that it is only the beginning of the Misty Mountains.

**Horizon on the way back:** In May they come here from Rivendell, dig up the trolls' gold and go on west into open country.

**Horizon in the game:** on the way there, the Misty Mountains with snowy peaks behind the forest line; on the way back, hills behind the forest.

**Weather**
- Rain: dark wet greens. Cloudy: oppressive.
- Clear: brighter woodland. In the book the Company sees the trolls in the bright morning after the night's fight.

**Time of day**
- Night: black woods; red firelight should show between the trees near the trolls (see below).
- Dawn: the most important hour in this region.

## The Stone Trolls – km 600

**Game:** Three troll sprites close to the left of the road (Bert, Tom and William).
Quote: *Dawn take you all, and be stone to you!*

**Book:** Three huge trolls sit around a large fire of beech logs, roasting mutton on long spits and drinking from jugs.
They argue all night about how to cook the dwarves, kept arguing by Gandalf, who throws his voice.
Then the dawn comes, and as the sun rises they turn to stone and stay in the clearing.
Their cave is nearby, behind a stone door, holding the swords Glamdring and Orcrist and the knife Sting.
On the way home the Company digs up the gold they buried here.

**Trail (book):** A clearing by the trolls' campfire, off the road. The trolls' trail leads uphill to their cave behind a stone door.

**Horizon on the way there:** Close woods, the clearing and the fire; no horizon at all.

**Horizon on the way back:** The same clearing, the trolls still standing as stone; the buried gold is dug up here.

**Weather**
- Any weather works; the trolls are stone.
- Rain: grey wet stone, almost like boulders.
- Clear: sunlight on the stone faces.

**Time of day**
- **Game:** at night on the way there, the trolls' campfire burns among them (emissive flames and a mutton spit).
  It is the book's scene, and in the dark the stone trolls look alive. By day, and on the way back, there is no fire.
- Dawn (04:30–07:30): the defining moment, "the light came up" and they turned to stone.
  **Idea:** a warm orange rim on the troll sprites at 05:30–06:30.
- Day: plain grey stone trolls.
- On the return trip (backwards) they stay stone in every light; the book has them still standing on the way home.

## The Ford of Bruinen – km 720

**Game:** A ford: the path is animated water and white foam with water on both sides; its edges are river water too (no grass verge or bank along it).
Quote: *The edge of the Wild.*

**Book:** The Ford of Bruinen is a Lord of the Rings name.
In The Hobbit, Gandalf says they are on the very edge of the Wild and must find the hidden valley.
They follow white stones, some covered in heather, to the brink of the steep valley.
Inside Rivendell they cross the river on a narrow stone bridge without a parapet.

**Trail (book):** The road disappears among heather and bogs and gullies; it is a hard, confusing land.
Gandalf follows white stones (some small, some half covered with moss or heather) to find the way.
Holes and ravines open suddenly at their feet.

**Horizon on the way there:** The Misty Mountains are close and high ahead; the hidden valley can't be seen until you stand at its edge.

**Horizon on the way back:** The open country to the west, falling away toward the Lone-lands.

**Weather**
- Clear: sparkling blue-white water.
- Rain: a fast, high, grey river. **Idea:** more white foam frames in rain.

**Time of day**
- Dusk: the book's party come down to Rivendell in the evening, so dusk fits.
- Night: dark water with moonlit foam.

## Rivendell Vale – km 725–745

**Game:** A green path along a gorge edge, pines growing below the lip, flowers.
Mountains and cliffs in the background.
Thin streams fall from notches in the valley walls on the horizon (part of the `cliffs` background layer).

**Book:** A hidden valley that opens suddenly at the foot of a steep fall.
The Company smells trees and hears water and elves singing ("O! What are you doing, and where are you going?").
The slopes are pine and then beech and oak lower down, with a pleasant feeling of evening.
Elves laugh at Bombur and the beards, and there is a fire in the house.

**Trail (book):** At the edge of the valley, a steep, zig-zag path goes down, and the ponies have to be led.
It goes through pines, then beeches and oaks, with a smell of trees, then to the river.
A narrow stone bridge without a parapet crosses the river.

**Horizon on the way there:** Inside the valley the sky is narrowed by the valley sides; the high mountains show above them to the east.

**Horizon on the way back:** In May, Bilbo and Gandalf come down into the valley from the mountains, and the valley is green below them.
Then they leave westward, the mountains at their backs.

**Horizon in the game:** cliffs in front of high mountains with snowy peaks, which fits both directions.

**Weather**
- Clear: soft, warm, peaceful. The book's mood is a summer evening.
- Cloudy: still pleasant.
- Rain: mild. **Idea:** lower rain weights here (Rivendell is a refuge) or lighter rain.

**Time of day**
- Dusk: the canonical arrival time, with gold light, lanterns in the trees and singing.
  **Idea:** use the `WINDOW` colour for small lanterns in the trees below the gorge lip.
- Night: lit windows of the elf houses and stars over the valley.
- Day: green and bright, waterfalls on the valley walls visible (done).

## Rivendell, the Last Homely House – km 739.8–740.1

**Game:** Five elf houses on the left between km 739.80 and 740.08, with lit windows.
Quote: *Tra-la-la-lally, here down in the valley!*

**Book:** Elrond's house is "a perfect house, whether you like food, or sleep, or story-telling, or singing".
The Company stays about two weeks, into Midsummer.
On Midsummer's Eve Elrond reads the moon-letters on Thror's map.
The letters can only be read by the light of a moon of the same shape and season as when they were written.

**Trail (book):** The valley path along the river to the house, with the elves singing in the trees.

**Horizon on the way there:** The house among trees, with the mountains rising above the valley.

**Horizon on the way back:** The same house, a welcome return.

**Weather**
- Clear: the best look. Rain and cloud should look softened, as the house is meant to be comfortable whatever the weather.

**Time of day**
- Dusk and night: windows glowing warm yellow (already done). The moon matters here.
  **Idea:** a crescent moon over the houses is a quiet nod to the moon-letters.
- Day: pale stone among green trees.

## The Misty Mountains – km 745–800

**Game:** Rock walls and gorges, snowy pines, snow on the wall tops and on the background peaks.
Weather: clear 20 %, cloudy 30 %, snow 30 %, storm 20 %.

**Book:** "Long days" of climbing on a narrow track, with a sheer fall on one side and a gloomy wall on the other.
Even in summer it is cold up here. There are passes, ravines and snow.

**Trail (book):** A narrow track: a sheer drop on one side, a gloomy cliff on the other.
They climb for days over rough stone; in some places there are no paths at all, only ravines and passes.
The air is thin and cold, even in summer.

**Horizon on the way there:** Peaks on peaks ahead. Looking back, Bilbo sees the lands they have left laid out far below.
Far away in the west, where everything is blue and faint, he thinks of his home.

**Horizon on the way back:** Gandalf and Bilbo cross in spring with Beorn's escort. Ahead to the west the lands open toward Rivendell, blue and far.

**Horizon in the game:** mountains in both layers, which fits both directions.

**Idea:** on the way there, an occasional gap in the walls showing the low, blue-green lowlands far below (the `valley` layer already draws this).

**Weather**
- Snow: the normal look; flakes drift across grey rock and white wall tops.
- Clear: cold, sharp, deep-blue sky and white peaks.
- Cloudy: peaks hidden. **Idea:** fade the far snowy peaks into the cloud colour when cloudy.
- Storm: see the High Pass.

**Time of day**
- Dawn and dusk: the peaks turn pink and orange (alpenglow) before the valleys. **Idea:** tint `HAZE_FAR_SNOW` warmer at dawn and dusk.
- Night: cold blue snow, stars very bright in the thin air.

## The High Pass and the thunderstorm – km 795–800 (landmark at 799)

**Game:** On the way there, the weather is forced to storm for the last 5 km: heavy rain, lightning bolts and white flashes.
On the way back the crossing has its normal mountain weather.
Quote: *Far over the Misty Mountains cold…*

**Book:** A thunderstorm, worse than any thunder-battle: lightning splinters on the peaks and the rocks shiver.
In the lightning flashes the Company sees stone-giants on the far side of the valley.
The giants hurl rocks at each other for a game, catch them, and toss them into the darkness below.
The party shelters in a dry cave, which turns out to be the goblins' Front Porch.
At night a crack opens in the back of the cave and the goblins carry them off.

**Trail (book):** The narrow pass, with rocks and the storm; they shelter in a cave that turns out to be the goblins' Front Porch.

**Horizon on the way there:** Nothing but darkness, rain and the lightning, which shows the stone-giants across the valley.

**Horizon on the way back:** In the book the return crossing is uneventful; clear spring views could be the reward.

**Weather**
- Storm, forced on the way there. It is the right choice.
- **Idea:** in each lightning flash, show a stone-giant silhouette for a moment on the far gorge side, or a boulder arcing across the sky.

**Time of day**
- Night is the canonical moment: the storm comes "in the dark".
  At night the scene should be black except for the flashes.
- **Idea:** if the player crosses by day, keep the sky very dark anyway (extra overcast or gloom between km 795 and 800).

## Goblin-town – km 800–812

**Game:** A tunnel with rock walls, pit-props and wall torches.
Gloom 0.55; nothing falls; weather is always "clear".
The rock face appears where the path enters the tunnel.

**Book:** The Front Porch leads to deep tunnels and a great cavern lit by a red fire in the middle.
Goblins hammer, crack whips and sing ("Clap! Snap! the black crack!").
Gandalf kills the Great Goblin; the lights go out, and the Company flees in the dark.
Dori drops Bilbo, who is lost on his own in the tunnels.

**Trail (book):** Tunnels sloping down, with the goblins driving the Company in the dark.
The great cavern has a red fire; then come endless winding passages.

**Horizon on the way there:** None; underground.

**Horizon on the way back:** None. In the book the return journey does not go through Goblin-town.

**Idea:** on the way back, keep the walls of the pass open to the sky instead of the tunnel.

**Weather**
- No weather underground, already done.
- **Idea:** turn the outside storm into faint thunder rumbles while in the tunnel.

**Time of day**
- Underground, time should not show at all: the same darkness, lit only by torches.
  **Game:** the tunnel uses a fixed cave light instead of the day/night light, with emissive torches, so it looks the same at noon and at midnight.

## Gollum's lake – km 806

**Game:** A landmark only (sign and banner), inside the tunnel.
Quote: *What has it got in its pocketses?*

**Book:** At the bottom of the tunnels lies a deep, dark, cold lake.
Gollum lives on a slimy island in the middle and paddles a little boat with his large flat feet.
He has two big round pale eyes, "lamp-like", that he uses to see in the dark.
Here Bilbo finds the Ring and wins the riddle game.

**Trail (book):** Bilbo crawls along a tunnel, finds the Ring on the floor, and comes down to the edge of cold, dark water.

**Horizon on the way there:** Total darkness; the lake can only be felt and heard.

**Horizon on the way back:** None.

**Weather**
- None, as it is underground.

**Time of day**
- Always pitch dark.
- **Game:** at km 805.9–806.1 the right-hand tunnel wall opens 13 m wide into a cavern over dark water (on the left on the way back), and Gollum's two pale eyes glow out on the lake.

## The Eastern Slopes – km 812–835

**Game:** Out of the mountain: pines, rock walls and gorges, with eagles circling overhead (km 813–845).
Weather: clear 60 %, cloudy 30 %, rain 10 %.

**Book:** Bilbo, now invisible, slips out of the back door into sunlight.
The Company goes down a steep slope, at sunset, to a clearing in a pine wood: the wargs' meeting-place.
They climb trees; the goblins set fire to the trees under them.
The Lord of the Eagles carries them off by moonlight.

**Trail (book):** Bilbo slips out through the back door, a narrow gap, into the sunlight.
The Company goes down a steep slope over loose stones, which slide and rattle down with them.
Then they go into a pine wood and a clearing.

**Horizon on the way there:** For the first time the lands east of the mountains are visible, spreading far below in the evening sun.

**Horizon on the way back:** The mountains rise ahead and above, high and cold, and the trail climbs toward them.

**Horizon in the game:** on the way there, flat lowlands behind a forest line; on the way back, the mountains.

**Weather**
- Clear: sunlight after the dark tunnel, the book's moment of escape.
- Cloudy and rain: allowed, but the scene is a clear evening.

**Time of day**
- Afternoon to sunset: the book's escape and descent.
- Night: the wargs' glade. **Idea:** glowing eyes among the trees (the Mirkwood `eyes` sprite) and the red glow of burning pines.
- Moonlit night: the eagles' rescue. **Idea:** at night, show the eagles against the moon.

## The Eagles' Eyrie – km 825

**Game:** A landmark; eagles circle over the region.
Quote: *Out of the frying-pan into the fire!*

**Book:** The eagles carry the Company to their eyrie, a broad shelf of rock high on the mountain-side.
They feed the Company and keep watch through the night.
In the morning they fly the Company over the land and set them down on the Carrock.

**Trail (book):** No trail: the eagles carry the Company to a rock shelf high on the mountain-side.

**Horizon on the way there:** From the eyrie: the whole land east of the mountains, the Great River glinting and a dark forest far away.

**Horizon on the way back:** The mountain-sides above, the eyrie somewhere among them.

**Weather**
- Clear: the wide view down over the Anduin valley.
- Cloud: the eyrie above the cloud; the valley below hidden.

**Time of day**
- Night: fire and the eagles' fierce eyes.
- Dawn: the flight to the Carrock.

## The Vale of Anduin and the Great River – km 835–875

**Game:** Flat, green, grassy land with reeds; mountains behind.
The Great River lies on the right between km 866 and 874.

**Book:** Wide open lands below the mountains, with the Great River flowing through them.
The Company finds itself in the morning on the Carrock in the middle of the river.

**Trail (book):** No trail: from the Carrock they walk over grass and through woods, following Gandalf, toward Beorn's house.

**Horizon on the way there:** Wide, open grassland; behind them the Misty Mountains, ahead far off a dark line of forest.

**Horizon on the way back:** The Misty Mountains rise ahead, white with spring snow.

**Horizon in the game:** on the way there, a dark line of forest far ahead; on the way back, the Misty Mountains over the hills.

**Weather**
- Clear: green meadows and a blue river under the mountains, a fresh morning look.
- Rain: soft and grey over the plain.

**Time of day**
- Dawn and day: the book's arrival.
- Night: dark, open and lonely.

## The Carrock – km 870

**Game:** A large rock on the right, 40 m away, next to the river.
Quote: *A great rock, almost a hill of stone.*

**Book:** A great rock, almost a hill of stone, standing in the river like the last outpost of the distant mountains.
Steps lead up to it, and there is a flat top with a cave.
Beorn made the steps; there is a ford of large flat stones from it to the bank.

**Trail (book):** Steps cut into the rock lead up to a flat top and a cave.
Beorn made them; a ford of flat stones crosses to the bank.

**Horizon on the way there:** From the top: the river, wide grasslands, the mountains behind and the woods ahead.

**Horizon on the way back:** The same rock in the river, the mountains close behind it.

**Weather**
- Clear: grey stone on a blue river, morning light.
- Rain: the rock dark and slick, the water rough.

**Time of day**
- Morning: the eagles drop the Company here at dawn.
- Night: a silhouette against the stars.

## Beorn's lands and Beorn's house – km 875–940 (hall at 890, beehives at 887–893)

**Game:** Meadows full of flowers, oaks, fences and 14 beehives near the hall.
Beorn's hall is on the left with lit windows.
Quote: *He is a skin-changer.*

**Book:** Beorn's grounds are surrounded by a tall thorn hedge.
Inside are big gardens and fields of clover and flowers alive with bees as big as hornets.
His wooden hall is long and low, with outbuildings, a wide central fire, posts and a low bench.
He keeps ponies, dogs and sheep that serve the table and walk on their hind legs.
At night Beorn goes out as a great bear and comes back at dawn.

**Trail (book):** Long walk over grass, then through oak woods, then a thick, tall thorn hedge.
Inside: flower fields and a wide wooden gate. The paths are straight and kept.
From Beorn's house, his ponies carry them to the forest. The path to the forest gate runs north of the Old Forest Road.

**Horizon on the way there:** Ahead to the east, the dark wall of Mirkwood grows larger day by day.
Behind, the Misty Mountains fade.

**Horizon on the way back:** Ahead, the Misty Mountains, white with snow; Bilbo and Gandalf stay for Yule and cross in spring.

**Horizon in the game:** on the way there, the black line of Mirkwood over green hills; on the way back, the snowy mountains.

**Weather**
- Clear: flowers, bees and summer warmth; the brightest look on the whole route.
- Cloudy: still rich colours.
- Rain: lush wet greens.
- On the return the Company spends Yule here. **Idea:** if seasons are added, the hall is the place for snow and firelight.

**Time of day**
- Day: bees visible around the hives. **Idea:** animated bee dots by day, none at night.
- Dusk and night: the hall's windows glowing with firelight.
  **Idea:** a huge bear silhouette moving at the edge of the fields at night.
- Dawn: Beorn returning from the bear-gathering.

## The Forest Gate – km 940

**Game:** An arch at the start of Mirkwood with a jagged forest face across the view.
Gandalf leaves here.
Quote: *Don't leave the path!*

**Book:** The gate is an arch made of two great trees leaning together, overgrown with ivy and lichen.
Inside, a narrow path leads into the dark.
Gandalf leaves the Company here and sends back the ponies, with the warning not to stray off the path.

**Trail (book):** Beorn's road ends at the eaves of the wood. The arch of two leaning trees is the start of a narrow path that winds into the dark.

**Horizon on the way there:** The black wall of the forest fills the whole horizon; the arch is the only opening.

**Horizon on the way back:** In the book the return does not use the forest path; Gandalf and Bilbo ride around the northern edge of Mirkwood.
Coming out at the gate, the open meadows and the Misty Mountains far ahead.

**Weather**
- Clear: the gate a black mouth against a sunny meadow, which is the right contrast.
- Rain: it barely matters; the forest is dark either way.

**Time of day**
- Day: the strongest contrast between the sunny meadow and the black arch.
- Night: almost invisible. **Idea:** draw the eyes at the edge of the gate at night.

## Mirkwood – km 940–1245

**Game:** Huge dark trees, webs, bushes and glowing eyes, with gloom 0.5 and a canopy across the sky.
Only a third of the rain gets through.
Weather: clear 60 %, cloudy 30 %, rain 10 %.

**Book:** Dark, silent and airless, a green-black twilight by day.
Black squirrels, and thick cobwebs stretched from tree to tree.
At night the darkness is total, and eyes are watching: pale, bulbous, insect-like eyes.
Big moths and bats swarm round any fire.
Water is scarce and food runs out.
The elves' woodland feasts show as lights and singing off the path, which vanish when anyone comes near.

**Trail (book):** A narrow path, often dim, winding, and overhung, which the Company must not leave.
The trees close in; the air is airless and still. The path gets hard to see in places.

**Horizon on the way there:** No horizon at all.
When Bilbo climbs a tall tree to look out, he sees only a sea of dark leaves in every direction, with black butterflies. He sees no edge, because the Company is in a dip in the forest.

**Horizon on the way back:** The same darkness. In the book they go around the northern edge of the forest instead.

**Idea:** for the return, either keep the forest (since the route is the same) or add a lighter, open edge on one side to suggest the northern route.

**Horizon in the game:** forest layers and the leaf canopy, which fits.

**Weather**
- Clear or cloudy should look nearly the same; the sky is barely visible, already handled by the canopy.
- Rain: a few drops getting through (already a third).
  **Idea:** remove the sun and moon behind the canopy, or only show a glimpse of them.

**Time of day**
- Day: a green twilight, already done by gloom.
- Night: total black except for the eyes, already done by the eyes palette.
  **Idea:** at night, flickering elf-feast torches deep among the trees that disappear as you approach.
- Dawn and dusk: should be hard to tell from day. A faint change in green is enough.

## The Enchanted River – km 1050

**Game:** A ford in the forest (water and foam across the path).
Quote: *Don't drink or bathe in it.*

**Book:** A strong, black stream crosses the path.
There is no ford or bridge, only a boat on the far side, which the Company drags across with a rope.
Bombur falls in, sinks into an enchanted sleep, and has to be carried for days.
On the other bank a white hart appears and the dwarves shoot their arrows in vain.

**Trail (book):** The path leads to the bank of a black stream. There is no bridge; a boat lies on the far side.
The Company pulls it over with a rope; Bombur falls in. After the river the path goes downhill into a dip.

**Horizon on the way there:** Forest walls on both sides and a gap of dim sky over the water.

**Horizon on the way back:** The same gap; a strip of sky over the river is the only light.

**Weather**
- Any. The water should always be black, not blue-white. **Game:** the river and the ford are black with dark-blue ripples.

**Time of day**
- **Idea:** a moving white deer at dusk; it is the only white thing in Mirkwood.
- Night: black water, invisible except for a few highlights.

## The Spiders' nests – km 1148–1152 (landmark at 1150)

**Game:** 60 webs and spiders in the trees on both sides.
Quote: *Attercop! Attercop!*

**Book:** The giant spiders' colony.
Webs are spun between the trees, and the dwarves hang in bundles, wrapped up.
Bilbo uses the Ring, names his sword Sting and taunts the spiders with *"Attercop!"* and *"Lazy Lob and crazy Cob"*.
The spiders' eyes glow in the dark.

**Trail (book):** The Company has left the path after the elves' feast lights and is lost among the trees.

**Horizon on the way there:** Only trees and webs; webs block the way between the trunks.

**Horizon on the way back:** The same.

**Idea:** narrow the path or make it fade into the ground here, since the Company is off the path.

**Weather**
- None noticeable.

**Time of day**
- Night: the spiders' glowing eyes. **Game:** the spiders' eyes use the `EYES` colour, so they glow at night.
- Day: the webs glint grey in the twilight. **Idea:** dew or grey highlights on the webs.

## The Elvenking's halls – km 1245–1250

**Game:** Gloom 0.3, mixed oaks and mirk-trees, and a stone gate at the right.
Quote: *Barrels out of bond.*

**Book:** A great cave with countless smaller ones opening off it, in a hill at the eastern edge of Mirkwood.
A river flows out from under the halls.
The gate has great stone doors, closed by magic.
The trees here are beeches, and the forest is lighter.
The elves feast and drink in torch-light.
The Company escapes in empty barrels through a water-gate into the river.

**Trail (book):** The elves bring the dwarves blindfolded through the forest to the halls.
A bridge crosses the river to the great stone doors.

**Horizon on the way there:** The forest gets lighter (beech trees) and a hill with the great doors rises ahead.

**Horizon on the way back:** Back into the dark forest.

**Weather**
- Lighter forest: clear and cloudy show some sky.
- Rain: the river high.

**Time of day**
- **Game:** two torches burn beside the doors.
- Night: the gate with its lights. The escape is at night, during a feast, while the guards sleep.

## The Forest River – km 1250–1400

**Game:** The river on the right with floating barrels and reeds, oaks and pines along the bank.

**Book:** The barrels float out from under the halls on the river, toward the Long Lake.
The river leaves the forest; the land opens and the sky grows wide.
Raft-elves gather the barrels into rafts and pole them downstream.

**Trail (book):** No trail: the Company floats in barrels, Bilbo riding on top of one.
At first the river runs fast in a tunnel and through the forest. Later it slows and widens through marshy land.
The raft-elves gather the barrels into rafts.

**Horizon on the way there:** The trees thin out and open land appears; the Lonely Mountain comes into view ahead.
The Mountain is the first sight that reminds the Company what they came for.

**Horizon on the way back:** The dark edge of Mirkwood ahead.

**Horizon in the game:** flat land behind a forest line; the Lonely Mountain is drawn ahead on the way there, as in the book.

**Weather**
- Clear: open sky after Mirkwood, a moment of relief.
- Cloudy and rain: autumn mood. In the book the season is turning to autumn here.

**Time of day**
- Night: the escape. **Idea:** the barrels' outlines in moonlight.
- Day: the rafts going downstream.

## The Long Lake and Lake-town, Esgaroth – km 1400–1420 (houses at 1412–1418)

**Game:** A plank causeway over open water.
Eighteen stilt houses stand on both sides with lit windows.
Erebor shows on the horizon.
Quote: *The King beneath the Mountain is returned!*

**Book:** A town built on wooden piles in the lake, joined to the shore by a great wooden bridge.
Lake-town is busy with trade and boats, and the Master's hall is there.
When the Company arrives the townsfolk feast and sing the old songs about the King under the Mountain coming back.
Later Smaug attacks and burns the town; Bard shoots him with the black arrow.

**Trail (book):** The rafts reach the lake; a long wooden bridge leads from the shore to the town on piles.

**Horizon on the way there:** Across the lake, the Lonely Mountain stands tall and alone in the north-east.
The far mountains of the Iron Hills could be faint behind.

**Horizon on the way back:** After the battle, the town is being rebuilt. Westward lies the lake and, far away, the dark line of Mirkwood.

**Horizon in the game:** on the way there, a low, distant mountain silhouette and the Lonely Mountain; on the way back, the dark line of Mirkwood to the west.

**Weather**
- Clear: the Lonely Mountain clear on the horizon across the lake, the key view.
- Cloudy: the mountain hidden in haze.
- Rain: the lake grey and flat.

**Time of day**
- Evening and night: the town lit up with lanterns and singing, already done with lit windows.
  **Idea:** reflections of lit windows in the water.
- Day: busy, with boats.
- **Idea:** on the return, if seasons or story states are modelled, show the burnt town: no lit windows, blackened piles.

## The River Running – km 1420–1470

**Game:** River on the left, grass, rocks and reeds, with the Mountain growing on the horizon.

**Book:** The Company goes up the River Running toward the Mountain by boat and pony.
The land becomes wild and bare, with the trees gone.

**Trail (book):** Up the river by boat, then on ponies along the bank, through grass that gets thinner.
Supplies come from Lake-town. The land becomes stony and bare.

**Horizon on the way there:** The Lonely Mountain ahead, growing larger, often dark and frowning in cloud.

**Horizon on the way back:** The Long Lake and its town, and Mirkwood behind it.

**Weather**
- Clear: the Mountain dominates the horizon.
- Cloud: the Mountain looming darkly in grey.

**Time of day**
- Dusk: the Mountain as a silhouette in front of the evening sky.
- Night: the Mountain black against the stars. **Idea:** a red glow at the peak, Smaug's fire inside.

## The Desolation of Smaug – km 1470–1527

**Game:** Stumps, dead trees, rocks and boulders on grey-brown ground.
Smaug circles in the sky from dusk to dawn on the way there; by day smoke drifts from the Front Gate.
Weather: clear 40 %, cloudy 50 %, rain 10 %.
Quote: *Never laugh at live dragons!*

**Book:** "Bleak and barren", with no bush or tree, only broken, blackened stumps of long-gone trees.
The ruined town of Dale lies in the valley before the Front Gate, burned by Smaug long ago.
Ravenhill is a lookout spur.
Smaug only leaves the Mountain at night, after Bilbo steals the cup.
On his last flight he goes to Lake-town and is killed there.

**Trail (book):** No trail: old roads are lost, and the ground is bare, with broken stones and blackened stumps.
The Company goes along the river toward the Mountain, then to the southern and western spurs.

**Horizon on the way there:** The Mountain fills the view, with long spurs reaching out like arms.
The ruins of Dale lie in the valley in front of the gate; Ravenhill stands on one spur.

**Horizon on the way back:** The bare land opening west toward the Long Lake.

**Horizon in the game:** the Lonely Mountain growing ahead on the way there; it switches to the textured close-up at km 1500. On the way back, flat land.

**Weather**
- Cloudy should be the normal look (already 50 %): smoke-grey, bleak and dead.
- Clear: still lifeless, harsh in the sun.
- Rain: the black ground wet.

**Time of day**
- Day: Smaug does not leave the Mountain by day in the book.
  **Game:** by day, smoke and steam drift out of the Front Gate (from 60 km out).
- Night: **Game:** Smaug flies from dusk to dawn, with bursts of fire.
- Dusk: the ruins of Dale as silhouettes.

## Erebor, the Lonely Mountain – km 1527–1530

**Game:** Rock walls and boulders, then open ground for the last 170 m up to the Front Gate: pillars and an arch in the mountain face.
The road goes in through it into a dark hall 30 m deep, 9 m wide and 9 m high, where the journey turns for home; walking out, the hall opens back onto the Desolation.
Gandalf is not with the Company on the way in; he joins Bilbo when the journey turns, as in the book, where he reappears only at the Battle of Five Armies.
The close-up mountain shows a lit west face and a shadowed east face.
Quote: *So comes snow after fire…*

**Book:** The Lonely Mountain stands alone, with spurs reaching out like arms.
The River Running flows from the Front Gate, a great dark arch with steam and smoke coming out.
On the west side is a secret door, which opens only on Durin's Day.
The last light of the setting sun shines on the keyhole and the thrush knocks.
The Battle of Five Armies is fought before the gate in winter.

**Trail (book):** The Front Gate is a great dark arch with the River Running flowing out of it.
On the west side, a narrow path and steps up a gully lead to a flat bay of grass and stone in front of the secret door.

**Horizon on the way there:** The rock face of the Mountain, and from the western spur the land falling away to the west.

**Horizon on the way back:** From the gate: the valley of Dale, the River Running and, far off, the Long Lake.

**Weather**
- Clear: the Mountain stark against the sky.
- Cloudy: the summit lost in cloud.
- Snow: on the return trip after the battle, winter. The quote "snow after fire" fits this.
  **Game:** on the way back, the Desolation and Erebor can roll snow.

**Time of day**
- Sunset: the defining moment. On Durin's Day the last light of the sun falls on the keyhole of the secret door.
  **Idea:** a gleam or a thrush on the west spur at 19:00–19:30.
- Night: the gate black, with a red glow inside while Smaug lives.
- Dawn: the battle and the gathering armies (as a story moment).

---

## The return journey

The game plays the same route backwards.
Gandalf walks with Bilbo all the way, the dwarves stay at the Mountain, and the Lonely Mountain is not drawn on the horizon.
In the book the return is mostly in winter and spring:

- At Beorn's they keep Yule.
- They cross the mountains in spring.
- They pass Rivendell in early summer (May), and collect the trolls' gold.
- They reach Bag End in early summer, to find an auction of Bilbo's things.

**Horizon, the whole way back (book):**
- Erebor to Mirkwood: the bare Desolation, then the Long Lake. The Mountain recedes behind.
- Around Mirkwood: the northern edge of the forest, a dark wall on one side and open land on the other.
- Beorn's to the Misty Mountains: the mountains rise ahead, snowy in winter and spring.
- Over the mountains: the green lands of the west open ahead.
- Rivendell to the Shire: Rivendell in May, then the empty Lone-lands, then the Shire in early summer.
- The last km: Bilbo's own Hill in the distance.

**Ideas** for the return trip:
- No Smaug in the Desolation, already done because he only flies on the way there.
- A burnt Lake-town.
- Snow at Erebor and in the Misty Mountains.
- The Shire in early summer.
