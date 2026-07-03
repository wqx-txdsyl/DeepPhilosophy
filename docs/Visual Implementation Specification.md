# DeepPhilosophy Visual Implementation Specification
# Version 3.0

---

# Part 01
# Project Vision
# The Museum of Human Thought

---

## 1. Project Position

DeepPhilosophy is **not** a conventional website.

It is not a documentation website.

It is not a timeline.

It is not a blog.

It is not an encyclopedia.

It should be built as a **Digital Museum of Human Thought**.

Users should feel that they are entering a museum rather than opening a webpage.

Every page should resemble a museum gallery.

Every philosophy school should resemble an exhibit.

Every civilization should resemble an independent exhibition hall.

---

## 2. Core Design Philosophy

The project should communicate one idea:

> Philosophy is not a collection of isolated schools.

It is a river.

Ideas originate.

Ideas branch.

Ideas merge.

Ideas disappear.

Ideas revive.

The entire website should visualize this process.

Time is only one dimension.

Geography is another.

Civilization is another.

Influence is another.

The interface should allow users to intuitively perceive this invisible network.

---

## 3. Visual Keywords

The entire project should consistently express the following atmosphere.

Ancient

Elegant

Timeless

Quiet

Academic

Museum

Epic

Historical

Civilized

Sacred

Natural

Layered

Immersive

Never use:

Cyberpunk

Game UI

Technology style

Glassmorphism

Neon

Cute illustration

Cartoon

Modern dashboard

Business style

Administration panel

---

## 4. Reading Priority

DeepPhilosophy is a reading experience.

Visuals exist only to support reading.

At every moment:

Readability

>

Navigation

>

Animation

>

Decoration

If any decorative element reduces readability,

remove it.

---

## 5. Content Priority

Never sacrifice information density for aesthetics.

Every philosophy school must remain visible.

Every timeline node must remain readable.

Every relationship graph must remain complete.

Beauty should organize information,

not replace information.

---

## 6. Asset Driven Development

From Version 3 onwards,

all visual design must be based on the existing Asset Library.

Claude Code is **strictly prohibited** from inventing new visual assets.

Instead,

it must compose scenes using the provided resources.

The philosophy of implementation is:

Small reusable assets

↓

Layer composition

↓

Environmental atmosphere

↓

Museum-quality interface

Instead of generating entirely new artwork.

---

## 7. Asset Root Directory

All visual resources are located under:

F:/philosophy/gene/

Claude Code should treat this folder as the single source of truth for all visual materials.

No duplicate assets should be created.

No replacement images should be generated unless explicitly requested.

---

## 8. General Rules

Visual assets may be:

Scaled

Blurred

Masked

Color-adjusted slightly

Opacity-adjusted

Layered

They may NOT be:

Redrawn

AI-regenerated

Color completely replaced

Stretched disproportionately

Converted into decorative clutter

Every asset should retain its historical dignity.

---

## 9. Layer Philosophy

The entire website should be composed using layers.

Layer 1

Paper texture

↓

Layer 2

World environment

↓

Layer 3

Civilization region

↓

Layer 4

River

↓

Layer 5

Terrain

↓

Layer 6

Landmarks

↓

Layer 7

Cards

↓

Layer 8

Interaction

↓

Layer 9

Light effects

↓

Layer 10

Particles

Every page follows this hierarchy.

---

## 10. Final Principle

When implementing any page,

Claude Code should first ask:

"What existing assets can be combined to build this scene?"

instead of

"What new design should I create?"

DeepPhilosophy is built by composing a museum,

not by continuously reinventing one.

# Part 02
# Asset Specification
# Visual Asset Library

---

## 2.1 General Principle

Every visual element in DeepPhilosophy must originate from the Asset Library.

Claude Code is forbidden from creating additional decorative illustrations.

If an effect can be achieved by combining existing assets,

always prefer composition over generation.

Every page should be assembled,

not painted.

---

# 2.2 Asset Root

Asset Root

gene/

Every visual resource must be loaded from this directory.

Do not duplicate assets.

Do not copy assets into other folders.

Always reference the original files.

---

# 2.3 Asset Hierarchy

The Asset Library is divided into the following categories.

gene/

atmosphere/

landmarks/

region/

river/

schools/

symbol/

terrain/

textures/

individual artwork

Each category has a dedicated purpose.

Assets must never be mixed arbitrarily.

---

# 2.4 atmosphere/

Purpose

Environmental atmosphere only.

Never use atmosphere assets as visible illustrations.

Allowed Usage

✓ Light rays

✓ Fog

✓ Dust

✓ Clouds

✓ Ambient glow

✓ Soft overlays

Forbidden

✗ Hero illustration

✗ Card background

✗ Timeline node

✗ Graph node

✗ Decorative stickers

Opacity

Recommended

5%

~

18%

Maximum

25%

Blend Mode

Screen

Soft Light

Overlay

Never use

Normal

100% Opacity

Multiply

unless explicitly required.

---

Files

effect_cloud.png

Large-scale environmental cloud layer.

May cover the entire viewport.

Should be heavily faded.

Recommended opacity

8%

effect_god_rays.png

Only used when highlighting important sections.

For example

Hero

Major Civilization

Museum Entrance

Do not overuse.

Maximum

2 occurrences

per page.

effect_golden_dust.png

Represents

history

memory

civilization

knowledge.

Should move slowly.

Particle speed

Very Slow

Opacity

6%

effect_light_leak.png

Used only near screen edges.

Never cover text.

Should remain almost invisible.

Opacity

5%

~

10%

effect_mist.png

Used between terrain layers.

Creates depth.

Never cover cards.

---

# 2.5 landmarks/

Purpose

Represent civilization.

Landmarks are NOT decorations.

They function as geographical anchors.

Every landmark should appear to belong naturally to the environment.

Never place landmarks floating in empty space.

Always integrate them into terrain.

Maximum

2 landmark assets

inside one viewport.

Do not build "collages."

---

Scale

8%

~

20%

Never exceed

25%.

Opacity

70%

~

100%

Blur

Allowed only for distant landmarks.

---

Recommended Placement

Near river

Mountain

Forest

Cliff

City silhouette

Never

Center of screen

Directly behind text

Behind important buttons

---

Example

Parthenon

↓

Ancient Greece Region

Only

Forbidden

China

Hero

Footer

Modern Philosophy

---

Confucian Temple

↓

China Region

Only

Forbidden

Western Philosophy

Europe

Hero

---

Oxford University

↓

Britain Region

Enlightenment

Analytic Philosophy

Only

---

Notre Dame

↓

Medieval Europe

Only

---

Nalanda University

↓

India Region

Only

---

Taj Mahal

Not a philosophy landmark.

Avoid using unless introducing Indian civilization as a whole.

Never use for Buddhist philosophy.

---

Great Wall

May appear only

inside China Region.

Should remain distant.

Avoid becoming visual focus.

---

Forbidden Rule

Never place multiple unrelated landmarks together.

Wrong

Parthenon

+

Forbidden City

+

Pyramid

Correct

One civilization

↓

One landmark

↓

One environment.

---

# 2.6 region/

Purpose

Large civilization background.

Region images define

space.

Not decoration.

Only one Region image may exist in one section.

Never stack two Region assets.

Region assets occupy

the lowest environmental layer.

Everything else should be built above them.

Scale

Cover

No Repeat

No Tile

No Rotation

Allowed

Mask

Blur

Brightness adjustment

Saturation adjustment

Forbidden

Perspective warp

Mirror

Heavy color grading

AI repainting

# 2.7 river/

Purpose

The River of Philosophy is the core visual identity of DeepPhilosophy.

It is NOT a decorative background.

It is NOT a separator.

It is NOT an illustration.

It is the primary spatial structure of the Timeline.

Every civilization exists because of the river.

Every philosophy school grows beside the river.

The river connects all knowledge.

---

Asset

gene/river/哲学之河2.0.png

This asset has the highest priority.

Always use

哲学之河2.0.png

Never use

哲学之河.png

unless explicitly requested.

---

Usage

Timeline Background

Museum Background

Long-scroll Civilization Page

Landing Transition

Never use for

Cards

Hero Illustration

Footer

Relationship Graph

Modal Background

Loading Screen

---

Scaling

Cover

Keep original aspect ratio.

Never stretch.

Never mirror.

Never rotate.

Never tile.

Never repeat.

---

Position

The river should always occupy the visual center of the page.

The page should be designed around the river.

Never place the river behind sidebars.

Never crop away the main flow.

The visible river should remain continuous.

---

Scrolling

The river should appear fixed in the world.

Cards scroll.

Timeline nodes scroll.

Content scrolls.

The river feels permanent.

Preferred implementation

background-attachment: fixed

or

independent parallax layer.

Parallax speed

0.15~0.25

Never move faster than the content.

---

Opacity

100%

Never reduce opacity globally.

Instead,

fade using masks.

---

Mask

Top

Fade into paper texture.

Bottom

Fade naturally.

Never cut the river abruptly.

---

Blur

Never blur the entire river.

Only distant sections may use

2px~4px

blur

to create depth.

---

Lighting

Do not recolor the river.

Only allow

Brightness

±10%

Contrast

±8%

Warm Tone

±5%

Never use

Blue neon

Purple

Cyberpunk

HDR

---

Relationship with Cards

Wrong

Card

↓

River

↓

Card

↓

River

Correct

River

↓

Cards grow beside it.

The river must never be interrupted.

Cards adapt to the river.

The river never adapts to cards.

---

Relationship with Timeline

Timeline nodes should never be drawn as a straight line.

The river itself is the timeline.

Do not render an additional central axis.

The river replaces the traditional timeline.

---

Relationship with Civilizations

Every civilization emerges naturally from the riverbank.

Ancient Greece

↓

Mediterranean side

China

↓

Yellow River basin

India

↓

Ganges basin

Islam

↓

Tigris and Euphrates basin

Civilizations should appear rooted in geography.

Never floating.

---

Allowed Decorations

Small rocks

River valley

Grass

Fog

Soft light

Tiny particles

Forbidden

Trees blocking the river

Large buildings inside the river

Icons floating above water

Large labels

---

Animation

The river should feel alive,

but almost motionless.

Allowed

Very slow shimmer

Soft flowing light

Tiny drifting particles

Morning mist

Forbidden

Visible flowing water animation

Wave simulation

Sparkles

Fantasy magic

---

Visual Emotion

The river represents

Time

Inheritance

Dialogue

Memory

Civilization

Continuity

It should evoke

calm

reflection

respect

rather than excitement.

---

Implementation Principle

Never ask

"How should I place the river?"

Always ask

"How should the page grow around the river?"

The river is the world.

Everything else is architecture.

# 2.8 schools/

Purpose

Every philosophy school is an exhibit.

Never design philosophy schools as ordinary UI cards.

Never imitate Material Design.

Never imitate Apple Cards.

Never imitate Dashboard Panels.

Each philosophy school should feel like a museum exhibit.

Users should feel that they are standing in front of an artifact.

The exhibit exists to present an intellectual tradition,

not a clickable rectangle.

---

Asset

gene/schools/

All philosophy school illustrations are stored here.

Every school page must use the corresponding artwork.

Never regenerate school illustrations.

Never crop important content.

Never replace them with placeholders.

---

Image Ratio

Preserve original ratio.

Recommended display

16:9

or

3:2

Do not stretch.

Do not mirror.

Do not rotate.

---

Image Placement

The school artwork occupies the upper portion of the exhibit.

Recommended proportion

35%

~

45%

of exhibit height.

The illustration introduces atmosphere.

The content introduces knowledge.

The illustration should never dominate the exhibit.

---

Frame

The exhibit should resemble a museum display case.

Recommended appearance

Warm white

Light ivory

Parchment

Bronze accent

Thin border

Very subtle shadow

Avoid

Dark cards

Heavy glass effects

Bright gradients

Rounded bubble style

Game UI

---

Background

Primary

Solid warm paper

Secondary

Very subtle parchment texture

Optional

gene/textures/

texture_parchment.png

Opacity

4%

~

8%

Never make textures obvious.

Users should feel them,

not notice them.

---

Typography

The philosophy school name

is the primary visual focus.

Recommended hierarchy

School Name

↓

Period

↓

Civilization

↓

Representative Philosophers

↓

One-sentence Introduction

↓

Explore

Do not overload the front side.

The exhibit should invite exploration.

---

Content Density

Each exhibit should remain compact.

Never place full descriptions.

Never display long paragraphs.

Recommended

4~7 information items.

---

Hover Interaction

Hover should feel like

approaching an exhibit.

Allowed

Slight elevation

Shadow increase

Image brightness +5%

Border highlight

Tiny scale

1.02

Maximum

1.03

Forbidden

Large pop-up animation

Flip cards

3D rotation

Bounce

Elastic effects

---

Click Interaction

Click should feel like

opening an exhibition room.

Transition should be slow.

Recommended

400ms

~

700ms

Fade

Scale

Cross dissolve

Avoid

Instant page jumps.

---

Relationship with Timeline

Every exhibit grows beside the river.

Do not align exhibits mechanically.

Wrong

Left

Right

Left

Right

Left

Right

Correct

Different distances

Different heights

Natural rhythm

Like villages along a river.

---

Spacing

Never let exhibits touch.

Recommended gap

120px

~

260px

Whitespace is part of the design.

Do not fear empty space.

---

Grouping

Philosophy schools belonging to the same civilization

should feel visually related.

Example

Ancient Greece

↓

Pre-Socratic

↓

Platonism

↓

Aristotelianism

↓

Cynicism

↓

Stoicism

↓

Epicureanism

These exhibits should visually resemble one another.

Shared palette.

Shared atmosphere.

Shared terrain.

---

Civilization Identity

Each civilization should have its own visual language.

China

Mountains

Bamboo

Academies

Yellow River

Warm ink colors

Greece

Marble

Olive trees

Mediterranean sunlight

Stone architecture

India

River

Temple

Forest

Golden mist

Islam

Courtyard

Geometry

Desert

Domes

Japan

Zen garden

Maple

Wood

Stone

Never mix identities.

---

Animation

Exhibits should appear

stable.

Heavy.

Timeless.

Avoid playful motion.

Allowed

Slow fade

Slow rise

Very gentle movement

Forbidden

Floating

Swinging

Pulsing

Continuous animation

---

Implementation Philosophy

The user is not selecting a menu.

The user is discovering an exhibit.

Every philosophy school deserves

the dignity of an independent museum display.

Claude Code should therefore ask:

"Would this feel appropriate inside a world-class museum?"

before implementing any school component.

If the answer is no,

redesign it.

# 2.9 terrain/

Purpose

Terrain is not decoration.

Terrain is philosophy.

Every philosophical tradition originates from a particular relationship between human beings and the world.

Terrain visualizes this invisible relationship.

Users may never consciously notice the terrain,

but they should always feel it.

The environment itself tells philosophy before any text appears.

---

Asset

gene/terrain/

terrain_mountains.png

terrain_forest.png

terrain_desert.png

terrain_plateau.png

terrain_river_valley.png

These assets should be treated as environmental foundations,

not illustrations.

---

General Rules

Terrain must always remain behind civilization.

Terrain supports regions.

Regions support schools.

Schools support content.

Never reverse this order.

---

Layer Order

Paper Texture

↓

Terrain

↓

Region

↓

River

↓

Landmark

↓

School Exhibit

↓

UI

↓

Atmosphere

Terrain never appears above UI.

Terrain never overlaps readable text.

---

Opacity

Recommended

12%

~

40%

Maximum

50%

The terrain should merge naturally into the page.

Never become the visual focus.

---

Mask

Terrain should fade naturally.

Hard edges are forbidden.

Always use

Gradient Mask

Brush Mask

Organic Fade

Never crop terrain into rectangles.

---

Scale

Large.

Terrain should feel continental.

Avoid small decorative mountains.

One mountain range

is preferable to

ten isolated hills.

---

Movement

Terrain does not move.

Terrain defines permanence.

Only atmospheric layers may move.

---

Terrain Identity

Every civilization owns a dominant terrain.

Never mix unrelated terrain.

---

China

Primary Terrain

terrain_mountains.png

Secondary

terrain_river_valley.png

Keywords

Mountain

River

Bamboo

Mist

Valley

Academy

Do not use

Desert

Large grasslands

European forest

---

Ancient Greece

Primary

terrain_river_valley.png

Secondary

Coastal cliff

Olive hills

Keywords

Mediterranean

Stone

Sea

Sunlight

Never use

Dense forest

Snow mountain

---

India

Primary

River Valley

Secondary

Forest

Plateau

Keywords

Ganges

Meditation

Sacred forest

Temple

Morning mist

---

Islamic Civilization

Primary

terrain_desert.png

Secondary

River Valley

Oasis

Keywords

Desert

Geometry

Courtyard

Knowledge

Stars

Never overuse sand.

The civilization is about wisdom,

not emptiness.

---

Japan

Primary

Forest

Secondary

Mountains

Keywords

Zen

Moss

Maple

Stone

Silence

---

Africa

Primary

Plateau

Grassland

River

Keywords

Savanna

Great Tree

Sunset

Origin

Life

---

Latin America

Primary

Plateau

Mountain

Forest

Keywords

Andes

Rainforest

Ancient ruins

Mist

---

Maya

Primary

Forest

Keywords

Dense Jungle

Temple

Stone

Nature

---

Tibet

Primary

Plateau

Mountain

Keywords

Snow

Sky

Silence

Distance

---

Mongolia

Primary

Plateau

Grassland

Sky

Huge Horizon

Wind

---

Terrain Transition

Different civilizations should blend naturally.

Never cut terrain sharply.

Example

Mountain

↓

Hill

↓

Valley

↓

River

↓

Forest

↓

Coast

The world should feel continuous.

---

Negative Space

Terrain should create empty space.

Empty space is valuable.

Never attempt to fill every area.

Allow the eye to rest.

---

Implementation Rule

When a page feels empty,

do not immediately add more graphics.

Instead,

first ask:

"Can terrain solve this?"

Most museum-quality interfaces rely on environmental composition,

not decoration.

---

Final Principle

Terrain is invisible architecture.

Users should remember

the feeling of a civilization,

not the mountain itself.

If users consciously notice the terrain,

it is already too strong.

# 2.10 textures/

Purpose

Textures define the physical material of the museum.

Users should feel that they are reading on

aged paper,

ancient maps,

historical manuscripts,

rather than digital panels.

Textures should never become visible decorations.

They should only influence perception.

The user should feel them,

not notice them.

---

Asset

gene/textures/

texture_parchment.png

texture_old_map.png

texture_paper_edge.png

texture_ancient_chart.png

texture_geometric_pattern.png

---

General Rules

Textures belong to

Material.

Not Content.

Never place textures

above text.

Never place textures

inside illustrations.

Never use textures

as standalone backgrounds.

Textures always work

through blending.

---

Layer Position

Paper Background

↓

Texture

↓

Terrain

↓

Region

↓

River

↓

Landmark

↓

Content

Textures should remain

below every visual element.

---

Opacity

Recommended

3%

~

10%

Maximum

12%

If users can immediately identify

the texture,

reduce opacity.

---

Blend Mode

Recommended

Multiply

Soft Light

Overlay

Never use

Normal

100%

Difference

Color Dodge

Hard Mix

---

texture_parchment.png

Purpose

The primary material of the museum.

Every reading page should feel as if it is printed

on archival parchment.

Recommended Usage

Timeline

School Page

Philosopher Page

Article Page

Knowledge Page

Never use

Hero

Loading Screen

Graph Canvas

Opacity

6%

Recommended.

---

texture_old_map.png

Purpose

Historical atmosphere.

Suggests exploration,

civilization,

journey.

Recommended Usage

Timeline

Civilization Section

Museum Entrance

Do not use

Cards

Buttons

Sidebar

Opacity

4%

~

8%

---

texture_paper_edge.png

Purpose

Page boundary only.

Never cover content.

Should only appear

near screen edges.

Used to soften digital borders.

Opacity

8%

Maximum.

---

texture_ancient_chart.png

Purpose

Ancient astronomical,

cartographic,

scientific feeling.

May appear

behind civilization maps.

May appear

inside Hero.

Never place behind paragraphs.

Avoid distracting readers.

Opacity

5%

Maximum.

---

texture_geometric_pattern.png

Purpose

Subtle civilization identity.

Should appear

only

inside related civilization sections.

Example

Islam

↓

Geometric Pattern

China

↓

Do NOT use.

Europe

↓

Do NOT use.

Opacity

3%

~

6%

Only.

---

Texture Frequency

Never stack

multiple obvious textures.

Wrong

Parchment

+

Old Map

+

Ancient Chart

+

Pattern

Correct

Primary Texture

+

One Supporting Texture

Maximum

2

textures

per viewport.

---

Paper Feeling

Every page should resemble

museum-quality paper.

Never resemble

PowerPoint

Dashboard

Modern App

News Website

Texture exists

to remove digital feeling.

---

Performance

All textures should load

once.

Reuse everywhere.

Never duplicate.

Use CSS background layers whenever possible.

Avoid repeated image requests.

---

Implementation Philosophy

Do not ask

"Which texture looks cool?"

Ask

"What material is this page made of?"

DeepPhilosophy is built

from paper,

stone,

wood,

and history.

Never from flat pixels.

# 2.11 symbol/

Purpose

Symbols are not icons.

Symbols are artifacts.

Every symbol represents the inheritance of human civilization.

They should never behave like modern UI icons.

Instead,

they should resemble museum objects,

historical tools,

or intellectual relics.

Users should feel that they are interacting with civilization,

not software.

---

Asset

gene/symbol/

symbol_scroll.png

symbol_quill.png

symbol_torch.png

symbol_compass.png

symbol_astrolabe.png

symbol_hourglass.png

symbol_ancient_book.png

symbol_bronze_vessel.png

symbol_olive_branch.png

symbol_laurel_crown.png

---

General Rules

Symbols are secondary.

Content is always primary.

Never place symbols simply to fill empty space.

Every appearance must carry meaning.

If a symbol cannot explain the content,

do not use it.

---

Rendering Style

Always preserve

the original illustration.

Never recolor into bright UI colors.

Preferred appearance

Bronze

Stone

Paper

Dark Gold

Ivory

Muted Brown

Avoid

Pure Black

Pure White

Blue

Purple

Bright Red

Neon

---

Opacity

Recommended

40%

~

90%

Decorative usage

20%

~

40%

Background watermark

5%

~

12%

---

Size

Small

Medium

Large

Recommended widths

16px

20px

24px

32px

48px

Avoid

64px+

unless used as hero decoration.

---

Shadow

Very subtle.

Recommended

1px

~

4px

Soft shadow.

Never floating.

Never glowing.

---

Animation

Symbols should feel

solid.

Heavy.

Historical.

Allowed

Very slow fade

Tiny opacity transition

Subtle brightness

Forbidden

Bounce

Rotate

Continuous spin

Shake

Pulse

Elastic motion

---

symbol_scroll.png

Meaning

Knowledge

Inheritance

Ancient texts

Recommended Usage

Article

Timeline Entry

Primary Source

Archive

Never use

Settings

Buttons

Navigation

---

symbol_quill.png

Meaning

Writing

Scholarship

Thought

Recommended Usage

Author

Philosopher

Essay

Commentary

---

symbol_torch.png

Meaning

Enlightenment

Discovery

Reason

Truth

Recommended Usage

Major milestone

Important philosophy

Civilization breakthrough

Never overuse.

Maximum

3

per page.

---

symbol_compass.png

Meaning

Exploration

Journey

Navigation

Recommended Usage

Timeline navigation

Civilization explorer

World philosophy map

Never use

Next button

Back button

---

symbol_astrolabe.png

Meaning

Science

Astronomy

Islamic Golden Age

Knowledge

Recommended Usage

Islam

Science

Ancient astronomy

Navigation of knowledge

---

symbol_hourglass.png

Meaning

Time

History

Era

Chronology

Recommended Usage

Timeline

Historical periods

Era labels

Never use

Loading animation.

---

symbol_ancient_book.png

Meaning

Classics

Scripture

Canon

Tradition

Recommended Usage

Book references

Classic works

Reading recommendation

Never use

Folder icon

Document icon

---

symbol_bronze_vessel.png

Meaning

Chinese Civilization

Ritual

Tradition

Order

Recommended Usage

Chinese Philosophy

Confucianism

Pre-Qin

Never use

Western sections.

---

symbol_olive_branch.png

Meaning

Ancient Greece

Peace

Dialogue

Academy

Recommended Usage

Greek philosophy

Academy

Humanism

Never use

China

Islam

India

---

symbol_laurel_crown.png

Meaning

Honor

Achievement

Master

Representative philosopher

Recommended Usage

Representative thinkers

Important philosophy schools

Special exhibitions

Never overdecorate.

---

Relationship with Civilization

Each civilization owns

its preferred symbols.

China

Bronze Vessel

Ancient Book

Scroll

Greece

Olive Branch

Laurel

Scroll

Islam

Astrolabe

Book

Compass

India

Book

Torch

Scroll

Rome

Laurel

Scroll

Torch

Japan

Book

Scroll

Minimal decoration

Avoid random combinations.

---

Decorative Principle

Wrong

Five icons

↓

One paragraph

Correct

One symbol

↓

One concept

↓

Enough whitespace

Museum quality depends on restraint.

---

Implementation Philosophy

Never ask

"Which icon should represent this?"

Ask

"If this object were placed inside a museum,

would visitors understand why it is here?"

Only then

should the symbol appear.

# 2.12 Independent Artwork
# Master Visual Assets

---

Purpose

These artworks represent the highest level visual identity of DeepPhilosophy.

Unlike ordinary assets,

they are not decorative resources.

They define the worldview of the entire museum.

Every artwork should be treated as a masterpiece.

Never overuse them.

Every appearance should feel meaningful.

---

Master Assets

gene/

civilization_silhouette.png

era_ancient.png

era_greece.png

era_medieval.png

era_renaissance.png

era_modern.png

gold_particles.png

old_map_texture.png

paper_texture.png

philosophy_symbols.png

philosophy_tree.png

哲学星图.png

---

General Principle

These assets belong to

Museum Identity.

Not UI.

Never repeat them frequently.

The rarer they appear,

the greater their impact.

---

# civilization_silhouette.png

Purpose

Represents the continuity of human civilization.

Use as a distant environmental silhouette.

Recommended Usage

Timeline

Civilization Introduction

Museum Entrance

Large Transition Sections

Never use

Cards

Dialogs

Navigation

Footer

Opacity

5%

~

12%

Blend

Multiply

Soft Light

Always blurred slightly.

Never appear as a sharp illustration.

---

# philosophy_tree.png

Purpose

Represents

the evolution of philosophy itself.

This is one of the symbolic images of the entire project.

Treat it as the Tree of Knowledge.

Recommended Usage

Homepage Hero

About Page

Museum Entrance

Philosophy Overview

Never use

Background decoration

Timeline

Cards

Sidebar

Maximum

One occurrence

per page.

Recommended Width

35%

~

55%

viewport width.

Never occupy the whole screen.

---

# 哲学星图.png

Purpose

Represents

the invisible relationships between ideas.

Not astronomy.

Not decoration.

It symbolizes

the universe of thought.

Recommended Usage

Hero Background

Knowledge Graph

Museum Entrance

Fade Transition

Opacity

4%

~

10%

Never become visually dominant.

The stars should almost disappear.

Users should feel

infinite space,

not outer space.

---

# philosophy_symbols.png

Purpose

Represents

civilizational knowledge.

Should only appear

during major transitions.

Never behind paragraphs.

Never inside cards.

Recommended

Museum Opening

Civilization Overview

Large Hero

---

# era_ancient.png

Purpose

Visual identity

of Ancient Philosophy.

Only use

inside

Ancient Era

sections.

Never mix

with Medieval

or Modern.

---

# era_greece.png

Purpose

Visual separator

for Greek civilization.

Should introduce

Ancient Greece,

never replace

Greek region artwork.

Use only once

within a continuous reading flow.

---

# era_medieval.png

Purpose

Transition

between Antiquity

and Medieval Philosophy.

Recommended

Large timeline milestones.

Never use

as decoration.

---

# era_renaissance.png

Purpose

Visual identity

for the Renaissance.

Use only

during the transition

from Medieval

to Modern philosophy.

Avoid repeated usage.

---

# era_modern.png

Purpose

Beginning

of modern thought.

May appear

at major timeline nodes.

Should feel

cleaner,

brighter,

more open

than previous eras.

---

# gold_particles.png

Purpose

Represents

the continuation

of civilization.

Not glitter.

Not magical effects.

Particles should resemble

dust floating

inside an old museum.

Animation

Extremely slow.

Opacity

3%

~

8%

Particle count

Very Low.

Never create

sparkling effects.

---

# paper_texture.png

Purpose

Global material.

Every page

should begin

with this texture.

It forms

the physical foundation

of the museum.

Recommended

Opacity

6%

Blend

Multiply

Never replace

with CSS colors alone.

---

# old_map_texture.png

Purpose

Represents

human exploration.

Recommended

Timeline

World Philosophy

Civilization Explorer

Knowledge Graph

Opacity

4%

~

8%

Do not place

behind dense text.

---

Visual Frequency

These assets

must remain rare.

Users should remember

seeing them.

Not become accustomed

to them.

A masterpiece

loses value

if repeated everywhere.

---

Relationship Between Assets

paper_texture

↓

defines material

old_map_texture

↓

defines exploration

civilization_silhouette

↓

defines civilization

哲学星图

↓

defines thought

philosophy_tree

↓

defines evolution

gold_particles

↓

defines memory

Together,

they construct

the identity

of DeepPhilosophy.

---

Implementation Philosophy

Claude Code should never ask

"What image can fill this space?"

Instead ask

"Does this section deserve one of the museum's master artworks?"

If the answer is uncertain,

do not use them.

Master artworks should be respected,

not consumed.

# Part 03
# Layout System
# Museum Architecture

---

## 3.1 Design Philosophy

DeepPhilosophy is not composed of webpages.

It is composed of museum spaces.

Every page should feel like entering another exhibition hall.

Users should never perceive abrupt transitions.

Instead,

they should feel that they are continuously walking inside the same museum.

The layout system therefore follows architectural logic,

not application logic.

---

## 3.2 Museum Structure

The entire website is divided into several permanent exhibition halls.

Entrance Hall

↓

Timeline Gallery

↓

Civilization Gallery

↓

School Exhibition Hall

↓

Philosopher Hall

↓

Knowledge Graph Hall

↓

Reading Room

↓

Archive

Each hall has its own atmosphere,

but all belong to one museum.

---

## 3.3 Visual Rhythm

Every page follows the same rhythm.

Large breathing space

↓

Hero

↓

Introduction

↓

Core Content

↓

Related Knowledge

↓

Explore More

↓

Footer

Never immediately display dense information.

Every page should have breathing space.

---

## 3.4 Grid System

Desktop

Maximum Content Width

1440px

Reading Width

960px

Ultra-wide monitors

Never allow text to exceed

1100px

Large whitespace should remain.

The museum should feel spacious.

---

Tablet

Content Width

90%

Viewport

---

Mobile

Content Width

92%

Viewport

Never create desktop shrink versions.

Design independently.

---

## 3.5 Vertical Rhythm

Recommended spacing

Section

↓

160px

Major Section

↓

240px

Minor Component

↓

48px

Paragraph

↓

24px

Never compress content vertically.

Museum reading requires breathing room.

---

## 3.6 Background System

Every page consists of multiple visual layers.

Layer 1

paper_texture

↓

Layer 2

terrain

↓

Layer 3

region

↓

Layer 4

river

↓

Layer 5

landmark

↓

Layer 6

content

↓

Layer 7

atmosphere

↓

Layer 8

particles

Every page follows exactly the same layer order.

Never rearrange.

---

## 3.7 Negative Space

Whitespace is content.

Never attempt to fill every area.

The museum should feel calm.

Large empty regions create visual dignity.

Whenever a page feels empty,

do not immediately add decorations.

Instead,

increase spacing.

---

## 3.8 Section Width

There are only three section widths.

Museum

100%

Gallery

1280px

Reading

960px

Avoid arbitrary widths.

Consistency creates order.

---

## 3.9 Cards

There are no Cards.

Every component is an Exhibit.

Every Exhibit belongs to a Gallery.

Never use dashboard terminology.

---

## 3.10 Navigation

Navigation should never dominate.

Recommended height

72px

Transparent

↓

Blur

↓

Paper Texture

↓

Thin bottom border

Scrolling

Navigation slowly becomes more opaque.

Never use heavy shadows.

Never use floating pills.

---

## 3.11 Borders

Avoid strong borders.

Preferred

1px

rgba(120,100,70,0.12)

Rounded Radius

16

20

24

Never exceed

28

Avoid exaggerated rounded corners.

---

## 3.12 Shadow

Every shadow should imitate museum lighting.

Recommended

0 12px 40px rgba(0,0,0,0.08)

Never

Black shadows

Hard shadows

Large floating cards

---

## 3.13 Color System

Primary Background

Warm Ivory

Secondary Background

Ancient Paper

Accent

Bronze

Deep Brown

Muted Gold

Primary Text

Near Black

Secondary Text

Warm Gray

Links

Deep Blue

Never use saturated colors.

The museum should feel aged,

not colorful.

---

## 3.14 Scroll Behavior

Scrolling should resemble walking.

Fast jumps are forbidden.

Every transition should feel continuous.

Recommended

scroll-behavior: smooth

Section Reveal

300~600ms

Never use

Full-page snapping.

---

## 3.15 Divider

Never use horizontal rules.

Instead,

create separation using

Whitespace

↓

Terrain

↓

Light

↓

Texture

↓

Civilization silhouette

The museum should have invisible boundaries.

---

## 3.16 Accessibility

Contrast

WCAG AA minimum.

Font size

Body

18px

Minimum

16px

Line Height

1.75

Reading always has priority.

---

## 3.17 Performance

Visible content only.

Lazy load all large images.

Every PNG should be GPU accelerated.

Avoid unnecessary repaint.

Target

60 FPS

on mainstream laptops.

---

## 3.18 Responsive Principle

Never hide important philosophical content.

On smaller screens

compress layout,

never remove information.

Images may shrink.

Text may wrap.

Knowledge must remain complete.

---

## 3.19 Design Principle

Claude Code should never ask

"How do I make this page look cooler?"

Instead ask

"How would a curator organize this exhibition?"

Every layout decision should resemble museum architecture,

not interface decoration.

# Part 04
# Hero System

---

## 4.1 Purpose

The Hero is not a banner.

It is the museum entrance.

Users should feel that they are standing before the gateway of human thought.

---

## 4.2 Composition

Background

paper_texture

↓

哲学星图（Opacity 6%）

↓

philosophy_tree（右侧，40%宽度）

↓

gold_particles（极少）

↓

Title

↓

Subtitle

↓

Explore Button

Never place large illustrations behind text.

---

## 4.3 Layout

Left

Title

Subtitle

Search

Actions

Right

Master Artwork

Whitespace

Never center everything.

Museum layouts prefer asymmetry.

---

## 4.4 Title

Maximum

2 lines

Very large

Elegant

Never use gradient text.

Never use outline.

---

## 4.5 Search

The search bar should resemble an archive retrieval system,

not a modern search engine.

Rounded rectangle

Paper background

Thin bronze border

No heavy shadow.

---

## 4.6 CTA

Only one primary action.

Explore Philosophy

or

Begin Journey

Never multiple competing buttons.

---

## 4.7 Motion

The Hero should almost stand still.

Only

Dust

Light

Tiny opacity

No floating objects.

No dramatic animation.

---

## 4.8 Scroll Hint

A subtle downward indicator.

Should resemble an ancient compass,

not a bouncing arrow.

# Part 05
# Timeline Gallery
# The River of Philosophy

---

## 5.1 Design Philosophy

The Timeline is not a timeline.

It is the central exhibition hall of DeepPhilosophy.

Users should not feel they are scrolling through dates.

They should feel they are walking alongside the River of Philosophy.

The river is history.

The schools are civilizations.

The philosophers are travelers.

The user is the explorer.

---

## 5.2 Core Principle

Traditional timelines use

↓

One vertical line

↓

Many dots

↓

Many cards

DeepPhilosophy completely abandons this model.

Instead,

the River itself becomes the timeline.

No additional central line should ever be drawn.

No timeline axis.

No timeline ruler.

No endless dots.

The river replaces all of them.

---

## 5.3 Background

Background composition:

paper_texture

↓

old_map_texture

↓

terrain

↓

region

↓

哲学之河2.0

↓

civilization silhouette

↓

mist

↓

content

↓

god rays

↓

gold particles

This order must never change.

---

## 5.4 Philosophy River

Always use

gene/river/哲学之河2.0.png

The river occupies the full page height.

Cover.

Center.

No repeat.

The river is fixed.

Content moves.

The world remains.

---

## 5.5 Timeline Length

The page may become extremely long.

This is encouraged.

Do not compress philosophy into a short page.

Long reading is intentional.

Users should feel the passage of history.

---

## 5.6 Era Structure

The timeline is divided into major historical eras.

Ancient World

↓

Classical Antiquity

↓

Late Antiquity

↓

Middle Ages

↓

Renaissance

↓

Early Modern

↓

Modern

↓

Contemporary

Every era is a museum room.

Never simply insert a title.

Instead,

allow atmosphere,

terrain,

and civilization

to transition gradually.

---

## 5.7 Era Artwork

Use

era_ancient.png

era_greece.png

era_medieval.png

era_renaissance.png

era_modern.png

only once.

Each artwork introduces an era.

Never repeat.

Never decorate.

Never tile.

Each acts as a chapter opening.

---

## 5.8 Civilization Transition

Civilizations should never abruptly appear.

Transition naturally.

Example

Mesopotamia

↓

Egypt

↓

Greece

↓

Rome

↓

Medieval Europe

↓

Renaissance

↓

Germany

↓

France

↓

Britain

↓

America

The environment should slowly evolve.

The user should almost not notice the transition.

---

China

↓

Pre-Qin

↓

Han

↓

Wei-Jin

↓

Tang

↓

Song

↓

Ming

↓

Qing

↓

Modern

also follows natural environmental evolution.

---

## 5.9 Region Background

Each civilization section

uses one

region image.

Only one.

Opacity

15%

~

30%

Always behind the river.

Never replace the river.

The river remains the protagonist.

---

## 5.10 Exhibit Placement

Exhibits should never align mechanically.

Avoid

Left

Right

Left

Right

Left

Right

Instead

allow

different offsets,

different elevations,

different distances,

like villages naturally forming beside a river.

The page should feel organic.

---

## 5.11 Exhibit Density

Dense periods

Ancient Greece

German Philosophy

Modern Philosophy

may contain many exhibits.

Sparse periods

should intentionally contain more empty space.

History has rhythm.

The interface should respect it.

---

## 5.12 Timeline Labels

Avoid giant year numbers.

Instead,

years should quietly accompany the river.

Recommended

Bronze

Small Caps

Light opacity

Never dominate the page.

Users are reading philosophy,

not chronology.

---

## 5.13 Civilization Sections

When entering a new civilization,

the user should immediately feel

a different atmosphere.

Not because of color.

Because of

terrain

light

architecture

mist

symbols

landmarks.

Civilization identity comes from environment.

---

## 5.14 Long Distance Reading

At any scroll position,

users should always see

three scales simultaneously.

Near

↓

Current school

Middle

↓

Nearby civilizations

Far

↓

The river disappearing into history.

This creates spatial depth.

---

## 5.15 Relationship Between Exhibits

Exhibits should never touch.

Whitespace represents

centuries,

oceans,

cultural distance.

Distance has meaning.

---

## 5.16 Scroll Experience

Scrolling should resemble

walking.

Never

falling.

Never

jumping.

Recommended speed

Slow.

Smooth.

Museum-like.

---

## 5.17 Timeline Navigation

Instead of

Back To Top

provide

Return To Source

represented by

the beginning of the river.

Navigation should become part of the narrative.

---

## 5.18 Hover

Hover should never interrupt reading.

Only

small elevation

slightly brighter artwork

slightly darker border

No dramatic animation.

---

## 5.19 Animation

Allowed

Fog drifting

Dust floating

Soft light

Very slow parallax

Forbidden

Flying cards

Water simulation

Sparkles

Glowing borders

Floating islands

Fantasy effects

---

## 5.20 Reading Flow

Every viewport should answer

three questions.

Where am I?

↓

Which civilization?

↓

Which philosophy?

↓

What came before?

↓

What comes next?

Users should never become lost.

---

## 5.21 Performance

Timeline images must all use

Intersection Observer.

Every large region image

lazy loads.

River

loads only once.

Particles use GPU.

Never repaint the river.

---

## 5.22 Responsive Layout

Desktop

The river remains central.

Tablet

River narrows.

Exhibits move closer.

Mobile

The river becomes the left guiding axis.

Exhibits stack naturally on the right.

Do NOT simply center everything.

---

## 5.23 Final Principle

Claude Code should never ask:

"How can I decorate this timeline?"

Instead ask:

"If this were a gallery inside the world's greatest philosophy museum,

how would visitors walk through history?"

Every implementation decision should support that experience.

# Part 06
# Civilization Gallery
# Exhibition Hall Design

---

## 6.1 Design Philosophy

Every civilization is an independent exhibition hall.

It is NOT a category.

It is NOT a folder.

It is NOT a filter.

Users should feel that they are entering another civilization.

The atmosphere,

lighting,

terrain,

architecture,

reading rhythm,

all change naturally.

Navigation remains consistent,

but the world changes.

---

## 6.2 Hall Structure

Each civilization follows exactly the same spatial rhythm.

Entrance

↓

Civilization Hero

↓

Overview

↓

Historical Context

↓

Major Schools

↓

Representative Philosophers

↓

Influence Network

↓

Timeline Position

↓

Related Civilizations

↓

Continue Journey

The order should never change.

Consistency creates familiarity.

---

## 6.3 Civilization Hero

Each civilization begins with a full-width environmental scene.

Use

gene/region/

Never generate new artwork.

Region images define atmosphere,

not information.

Text should occupy

no more than

40%

of the Hero.

The illustration remains dominant.

---

## 6.4 Environmental Identity

Every civilization owns its own atmosphere.

China

Mountain

Mist

River

Academy

Warm Ink

Greece

Sea

Marble

Sunlight

Olive

Stone

Rome

Architecture

Order

Forum

Road

Column

India

Forest

Temple

River

Morning Light

Islam

Courtyard

Geometry

Stars

Desert

Japan

Zen Garden

Wood

Stone

Silence

Africa

Savanna

Great Tree

Earth

Warm Sunset

Never mix identities.

---

## 6.5 Reading Rhythm

Information should become progressively denser.

Beginning

Visual

↓

Middle

Balanced

↓

End

Knowledge-rich

The user first experiences,

then understands,

then studies.

---

## 6.6 Related Civilizations

Never simply display

"Related".

Instead explain

Historical Influence.

Example

Ancient Greece

↓

Rome

↓

Medieval Europe

↓

Renaissance

↓

Modern Europe

Users should always understand

how ideas travelled.

---

## 6.7 Transition

Leaving one civilization

should resemble leaving one exhibition room

and entering another.

Never abruptly switch backgrounds.

Always use

light,

terrain,

river,

and atmosphere

to connect them.

# Part 07
# School Exhibition Hall

---

## 7.1 Philosophy

A philosophy school is not an article.

It is an exhibition.

Users should discover it.

Not simply read it.

---

## 7.2 Structure

Hero

↓

Core Concept

↓

Historical Background

↓

Representative Thinkers

↓

Timeline

↓

Relationship Graph

↓

Major Works

↓

Influence

↓

Legacy

↓

Continue Exploration

---

## 7.3 Hero

Background

School Artwork

↓

Very subtle atmosphere

↓

School Name

↓

One Sentence

↓

Metadata

Never place long introductions.

---

## 7.4 Metadata

Display only

Era

Civilization

School Type

Time Span

Representative Thinkers

Never overload Hero.

---

## 7.5 Knowledge Density

As users scroll,

knowledge density gradually increases.

Top

Visual

↓

Middle

Conceptual

↓

Bottom

Academic

The deepest information belongs at the end.

---

## 7.6 Related Schools

Never recommend randomly.

Use actual influence.

Example

Stoicism

↓

Roman Stoicism

↓

Christian Thought

↓

Existentialism

Connections should teach history.

---

## 7.7 Major Works

Treat books like museum artifacts.

Do not render them as shopping cards.

Display

Title

↓

Author

↓

Importance

↓

One Sentence

# Part 08
# Philosopher Hall

---

## 8.1 Philosophy

A philosopher page should resemble

a portrait gallery.

Not a biography.

The visitor should first meet the thinker,

then understand the thinker.

---

## 8.2 Hero

Large portrait.

Whitespace.

Name.

Birth & Death.

School.

One quotation.

Nothing more.

Silence creates respect.

---

## 8.3 Reading Order

Life

↓

Ideas

↓

Major Works

↓

Historical Context

↓

Influence

↓

Students

↓

Teachers

↓

Related Schools

↓

Timeline

---

## 8.4 Portrait

Portraits should never be cropped aggressively.

Eyes should remain visible.

Avoid circular avatars.

Museum portraits deserve frames,

not profile pictures.

---

## 8.5 Quotations

One quotation only.

Never overload.

Large typography.

Wide whitespace.

# Part 09
# Knowledge Graph

---

## 9.1 Philosophy

The graph represents

the universe of philosophy.

Not a database.

Relationships should feel alive.

---

## 9.2 Background

paper_texture

↓

old_map_texture

↓

哲学星图

↓

graph

Never use white background.

Never use dark mode.

---

## 9.3 Nodes

Nodes should resemble stars.

Not circles.

Not buttons.

Not avatars.

Each node emits

very subtle

warm light.

---

## 9.4 Edges

Edges should resemble

constellation lines.

Thin.

Elegant.

Semi-transparent.

Never thick.

Never colorful.

---

## 9.5 Clusters

Clusters emerge naturally.

Do not force circular layouts.

Civilizations naturally gather.

Schools naturally gather.

Time naturally stretches.

---

## 9.6 Camera

Default

Zoomed out.

Users first perceive

the universe.

Then explore details.

---

## 9.7 Interaction

Hover

↓

Highlight

↓

Fade others

↓

Show Preview

Never open dialogs immediately.

# Part 10
# Explorer

---

Users do not search.

Users explore.

Search UI should resemble

museum archive retrieval.

Results should be grouped by

School

↓

Philosopher

↓

Civilization

↓

Book

↓

Era

Never display a flat result list.

# Part 11

Every animation exists

to support reading.

Never entertain.

Animation should disappear.

Standard Durations

Hover

180ms

Card

250ms

Section

400ms

Hero

800ms

Never exceed

1000ms

Never use

Bounce

Elastic

Shake

Rotate

# Part 12

Body

18px

Line Height

1.75

Paragraph Width

70 characters

Never use justified text.

Always left align.

Chinese and English should use independent font stacks.

Headings must maintain a clear hierarchy.

Avoid excessive font weights.

Museum typography values calmness over impact.

# Part 13
# Component Design System

---

## Philosophy

DeepPhilosophy should never be built from generic UI components.

There are no cards.

No panels.

No widgets.

No modules.

Every component belongs to the museum.

Every component should appear handcrafted.

The user should never recognize the design system.

Instead,

they should remember the museum.

---

# 13.1 Component Hierarchy

There are only six levels of components.

Museum

↓

Gallery

↓

Exhibit

↓

Artifact

↓

Annotation

↓

Interaction

Everything belongs to one of these levels.

No exceptions.

---

# 13.2 Museum

Museum represents the entire page.

Only one Museum exists.

Museum controls

background

lighting

river

terrain

atmosphere

Museum never contains business logic.

It only controls spatial experience.

---

# 13.3 Gallery

Gallery groups Exhibits.

Examples

Timeline Gallery

Civilization Gallery

Philosopher Gallery

School Gallery

Gallery defines rhythm.

Never decoration.

---

# 13.4 Exhibit

The most important component.

Everything meaningful is an Exhibit.

Examples

School

Civilization

Book

Thinker

Timeline Event

Relationship Cluster

Exhibits deserve whitespace.

Never place Exhibits tightly together.

---

# 13.5 Artifact

Artifact is a supporting object.

Examples

Ancient Book

Compass

Laurel

Scroll

Astrolabe

Artifacts never become buttons.

Artifacts never replace icons.

Artifacts explain culture.

---

# 13.6 Annotation

Annotations explain.

Examples

Date

Era

Tag

Civilization

Metadata

Small descriptions

Annotations should disappear visually.

Content remains dominant.

---

# 13.7 Interaction

Buttons

Search

Navigation

Hover

Filters

All belong to Interaction.

Interactions should remain quiet.

Users should almost forget they exist.

---

# 13.8 Whitespace

Whitespace is a component.

Treat empty space

as carefully

as visible content.

Never fill gaps.

---

# 13.9 Visual Weight

Each viewport

must contain

only one

visual focus.

Everything else

supports it.

Never create visual competition.

---

# 13.10 Component Depth

Every component belongs to

one of three depths.

Background

Middle

Foreground

Never invent more layers.

Users understand depth naturally.

---

# 13.11 Borders

Avoid borders.

Whenever possible,

replace borders with

light,

shadow,

spacing.

Museum objects rarely have outlines.

---

# 13.12 Shadows

Shadow represents

distance,

not decoration.

Closer

↓

Darker

Farther

↓

Lighter

Never exaggerate.

---

# 13.13 Corners

Museum furniture

rarely uses

perfect circles.

Recommended Radius

12

16

20

24

Never Pills.

Never Capsules.

---

# 13.14 Glass

Glassmorphism

Forbidden.

Deep blur

Forbidden.

Heavy transparency

Forbidden.

Museum materials are

paper,

wood,

bronze,

stone.

Not acrylic.

---

# 13.15 Gradients

Gradients should simulate

light,

never branding.

No rainbow.

No colorful hero.

No neon.

---

# 13.16 Motion

Components never perform.

Components respond.

Motion exists because

the user acted.

Not because

the page wants attention.

---

# 13.17 Hover

Hover resembles

approaching an exhibit.

Allowed

2% Scale

Soft Light

Slight Elevation

Forbidden

Bounce

Rotate

Glow

3D

Flip

---

# 13.18 Click

Click resembles

opening a display cabinet.

Slow.

Respectful.

Never explosive.

---

# 13.19 Loading

Loading should resemble

museum preparation.

Skeletons

Paper fade

Soft dissolve

Never spinning neon loaders.

---

# 13.20 Empty State

An empty area

is not failure.

It is silence.

Use

terrain

light

quotes

instead of illustrations.

---

# 13.21 Error State

Never show

technical language.

Instead

guide users naturally.

Museum tone.

Not engineering tone.

---

# 13.22 Scroll

Scroll equals

walking.

Every section

should feel reachable.

Never endless.

Never compressed.

---

# 13.23 Scale

Everything follows

human reading scale.

Never gigantic.

Never miniature.

Museum proportions

over software proportions.

---

# 13.24 Reuse

One component

↓

Many contexts.

Never duplicate.

Variation comes from

content,

not implementation.

---

# 13.25 Final Principle

Claude Code should never ask

"Which React component should I use?"

Instead ask

"What kind of museum object am I building?"

If the answer is unclear,

the component has not yet been designed.

# Part 00.5
# Anti-Patterns
# Forbidden Design Language

---

## Philosophy

The fastest way to destroy DeepPhilosophy

is not poor code.

It is choosing the wrong visual language.

Claude Code should first learn

what NOT to build.

Only then

should it begin implementation.

---

# Never Become

DeepPhilosophy is NOT

a Dashboard.

a CMS.

a SaaS.

an Admin Panel.

a Documentation Website.

a Blog.

a Knowledge Base.

a Wiki.

an AI Chat Application.

a Material Design Demo.

a Bootstrap Theme.

---

# Never Use

Glassmorphism

Neumorphism

Cyberpunk

Futurism

Gaming UI

Crypto UI

Web3 Style

AI Gradient Style

Apple Vision Pro imitation

Liquid Glass

Windows Fluent

Excessive Blur

Heavy Transparency

Neon

RGB Lighting

Rainbow Gradient

Large Floating Cards

Oversized Icons

Emoji Decoration

Animated Backgrounds

Particle Storms

Lottie Everywhere

---

# Never Feel Like

Notion

Linear

Slack

Discord

Jira

Confluence

ClickUp

Figma

ChatGPT

Claude

GitHub

These are excellent software.

DeepPhilosophy is not software.

It is a museum.

---

# Never Layout Like

Pinterest

Card Wall

Dashboard Grid

Infinite Masonry

Bootstrap Rows

App Home Screen

News Portal

Every page should feel curated.

Never algorithmic.

---

# Never Animate

Bounce

Elastic

Shake

Flip

Rotate 360°

Flying Objects

Exploding Cards

Parallax Abuse

Mouse-follow Effects

Confetti

Fireworks

---

# Never Color

Pure Black

Pure White

Pure Red

Pure Blue

Pure Green

Purple Neon

High Saturation

Everything should feel

aged,

warm,

historical.

---

# Never Space

Tiny gaps.

Crowded cards.

Dense UI.

Whitespace is mandatory.

---

# Never Decorate

Do not add graphics

simply because space exists.

Every object

must explain civilization.

---

# Never Generate

Placeholder illustrations.

AI clipart.

Stock icons.

Random landscapes.

Every artwork

must correspond

to the project's asset library.

---

# Never Ignore

The River.

The River is always

the protagonist.

If another element

becomes more visually dominant,

the design has failed.

---

# Final Question

Before writing any component,

Claude Code should ask:

"If I remove all text,

would this still resemble

a world-class philosophy museum,

or merely another React website?"

If the answer is

"React website",

redesign it completely.

# Part 01
# Narrative System
# The Journey of Thought

---

## Philosophy

DeepPhilosophy is not a database.

It is not a search engine.

It is not an encyclopedia.

It is a journey.

The visitor should never feel

"I am looking up philosophy."

Instead,

they should feel

"I am travelling through the history of human thought."

Everything exists

to support this journey.

---

## Chapter Structure

Every page tells a story.

Every story follows the same rhythm.

Arrival

↓

Observation

↓

Understanding

↓

Connection

↓

Reflection

↓

Departure

Never skip any stage.

---

## Arrival

The first screen

never teaches.

It welcomes.

Users first experience

the atmosphere.

Only afterwards

do they begin learning.

Emotion always comes before knowledge.

---

## Observation

The user begins noticing

objects,

landmarks,

civilizations,

schools.

The interface should encourage

curiosity.

Not explanation.

---

## Understanding

Only after curiosity appears

should dense information appear.

Users should feel

"I want to know."

Never

"You must know."

---

## Connection

Every page must answer

three questions.

Where did this idea come from?

↓

Who continued it?

↓

Who opposed it?

Knowledge should become a network,

not isolated facts.

---

## Reflection

Every important page

should end

with space.

Whitespace.

One quotation.

One image.

Silence.

Users should think,

not immediately click elsewhere.

---

## Departure

Every page should naturally suggest

the next destination.

Never say

"You may also like."

Instead,

continue the journey.

Examples

From Plato

↓

Aristotle

↓

Neoplatonism

↓

Christian Philosophy

The visitor should never become lost.

---

## Emotional Curve

Every page follows

the same emotional curve.

Curiosity

↓

Wonder

↓

Understanding

↓

Connection

↓

Contemplation

↓

Exploration

The user should never experience

information overload.

---

## Narrative Continuity

No page exists independently.

Every page belongs

to the same museum.

Every transition

is another room.

Never another website.

---

## Narrative Principle

If a section

cannot answer

"Why is this here?"

remove it.

Everything should advance

the visitor's journey.

Nothing exists

only to occupy space.

# Part 15
# Museum Lighting System

---

## 15.1 Philosophy

Light is the invisible guide of the museum.

Visitors should not consciously notice lighting.

Instead,

they should subconsciously feel changes in time,

civilization,

and atmosphere.

Light replaces color as the primary emotional language.

---

## 15.2 General Principles

Lighting is environmental.

Never spotlight UI.

Never create dramatic stage effects.

Light always appears natural.

It should resemble sunlight,

window light,

mist,

or reflected stone.

---

## 15.3 Layer Order

Background

↓

Terrain

↓

Region

↓

Lighting

↓

River

↓

Landmarks

↓

Content

↓

Atmosphere

Light always remains beneath content.

---

## 15.4 China

Diffuse morning light.

Mountain mist.

Warm ivory.

Soft shadows.

No obvious light source.

---

## 15.5 Ancient Greece

Mediterranean afternoon.

Bright stone reflection.

Warm sunlight.

Clear sky.

Long shadows.

---

## 15.6 Rome

Golden sunset.

Architectural shadows.

Warm marble.

Slight orange reflection.

---

## 15.7 Medieval Europe

Cathedral window light.

Soft blue-gray atmosphere.

High contrast only near stained glass.

Everything else remains dim.

---

## 15.8 Renaissance

Warm studio lighting.

Oil painting atmosphere.

Soft directional sunlight.

Balanced contrast.

---

## 15.9 Enlightenment

Large window light.

Paper becomes brighter.

Visual openness increases.

---

## 15.10 German Philosophy

Cold afternoon sunlight.

Gray-blue atmosphere.

Low saturation.

Long winter shadows.

---

## 15.11 France

Soft urban daylight.

Elegant.

Neutral.

Slight golden tone.

---

## 15.12 Britain

Cloudy daylight.

Cool white.

Low contrast.

Moist atmosphere.

---

## 15.13 America

Bright museum lighting.

Modern.

Clean.

Neutral white.

---

## 15.14 India

Golden morning mist.

Temple light.

Warm humidity.

Soft diffusion.

---

## 15.15 Islam

Courtyard skylight.

White stone reflection.

Geometric shadows.

High clarity.

---

## 15.16 Japan

Overcast sky.

Zen garden.

Very soft contrast.

Balanced grayscale.

---

## 15.17 Africa

Warm sunset.

Earth reflection.

Dust in sunlight.

Long shadows.

---

## 15.18 Latin America

Rainforest sunlight.

Mist.

Green reflected light.

Warm humidity.

---

## 15.19 Transition

Lighting should interpolate gradually.

Never switch instantly.

Average transition

800~1600px scroll distance.

---

## 15.20 Animation

Light never flickers.

Only

Opacity

Intensity

Direction

change slowly.

---

## 15.21 Performance

Lighting uses

CSS gradients

mask-image

mix-blend-mode

Avoid heavy filters.

---

## 15.22 Final Principle

Visitors remember

the feeling of a civilization,

not the light itself.

# Part 16
# Soundless Interaction

---

## Philosophy

Every interaction should be silent.

The interface should never demand attention.

Interaction supports contemplation.

---

Hover

Soft.

Click

Gentle.

Scroll

Continuous.

Search

Quiet.

Transition

Natural.

Nothing should interrupt reading.

---

Buttons

Never pulse.

Never flash.

Never vibrate.

---

Hover Scale

1.02

Maximum

1.03

---

Click

Opacity

↓

Scale

↓

Open

No bounce.

---

Scroll

No scroll-triggered explosions.

No dramatic reveals.

Only gentle fade.

---

Page Transition

Fade

↓

Scale

↓

Content

Never slide entire pages.

---

Loading

Paper fades in.

Images dissolve.

No spinner unless absolutely necessary.

---

Notifications

Avoid.

If necessary,

display as museum annotation,

not toast messages.

---

Final Principle

Interaction should disappear.

Users remember philosophy,

not animations.

# Part 17
# Visual Consistency Checklist

Every page must satisfy all items before completion.

□ River remains the primary visual structure.

□ Region identity is recognizable.

□ Terrain supports atmosphere.

□ Lighting matches civilization.

□ Texture remains subtle.

□ Whitespace is sufficient.

□ Only one visual focus exists.

□ Typography remains readable.

□ No dashboard appearance.

□ No SaaS appearance.

□ No Material Design appearance.

□ No Bootstrap appearance.

□ No unnecessary borders.

□ No unnecessary shadows.

□ No unnecessary gradients.

□ No repeated illustrations.

□ Museum atmosphere maintained.

□ Timeline remains continuous.

□ Images never obscure text.

□ Every exhibit has breathing space.

□ Every transition feels architectural.

If any item fails,

the page should be redesigned.

# Part 18
# Exhibition Composition System

---

## 18.1 Philosophy

Every screen is an exhibition composition.

Not a web page.

The visitor should always understand

where to look first,

where to look second,

and where to continue.

Visual hierarchy is more important than visual decoration.

---

## 18.2 Three-Layer Composition

Every viewport consists of three layers.

Foreground

Current Exhibit

↓

Middle Ground

Related Civilization

↓

Background

River

Terrain

Atmosphere

The foreground changes.

The background tells history.

---

## 18.3 Focus Principle

Every screen has only one focus.

Never allow two elements to compete.

Priority

Title

↓

Artwork

↓

School Card

↓

Graph

↓

Decoration

---

## 18.4 Reading Path

Desktop

Top Left

↓

Center

↓

Right

↓

Bottom

Mobile

Top

↓

Image

↓

Content

↓

Related

The reading path should feel effortless.

---

## 18.5 Golden Ratio

Large sections should approximately follow

38%

↓

62%

or

40%

↓

60%

Avoid perfect symmetry.

Museums rarely feel symmetrical.

---

## 18.6 Empty Space

Empty space is intentional.

Never fill blank areas with icons,

particles,

or random graphics.

If the page feels empty,

increase breathing room.

---

## 18.7 Visual Weight

Illustrations

High

River

Medium

Landmarks

Medium

Typography

High

Decoration

Low

Decoration should never exceed content.

---

## 18.8 Depth

Depth should come from

opacity,

blur,

lighting,

and spacing.

Never fake depth using exaggerated shadows.

---

## 18.9 Eye Rest

Every long page must contain

visual resting points.

Methods

Large whitespace

↓

Landscape

↓

Quotation

↓

Transition image

↓

River widening

Never present uninterrupted information for thousands of pixels.

---

## 18.10 Balance

Every viewport should balance

Image

↓

Knowledge

↓

Whitespace

No viewport should contain only text.

No viewport should contain only illustrations.

---

## 18.11 Final Principle

Composition should guide the visitor

without being noticed.

If users consciously notice layout,

it is probably overdesigned.

# Part 19
# Image Usage Rules

---

## Philosophy

Images are historical evidence,

not decoration.

Every image must explain philosophy.

Never add images simply to increase visual richness.

---

## Image Priority

1

Region Artwork

2

School Artwork

3

Landmark

4

Master Artwork

5

Symbols

6

Atmosphere

Never reverse this order.

---

## Image Frequency

One large illustration

per viewport.

Maximum.

Avoid visual overload.

---

## Image Crop

Never crop important architecture.

Never crop philosopher faces.

Never stretch.

Never distort.

Maintain original aspect ratio whenever possible.

---

## Image Overlay

Text should always remain readable.

Recommended

Gradient Mask

instead of dark overlays.

---

## Opacity

Large background illustration

15%

~

30%

Master artwork

5%

~

15%

Decorative element

5%

~

10%

---

## Blending

Preferred

Multiply

Soft Light

Overlay

Avoid

Normal

100%

Difference

Hard Light

---

## Color

Images should share

one unified color temperature.

Never mix cold blue images

with warm parchment

on the same screen.

---

## Resolution

Desktop

Minimum

2560px

Hero

3840px preferred.

Avoid blurry assets.

---

## Lazy Loading

Every image below the fold

must lazy load.

Hero image

preload.

River

load once.

---

## Repetition

Never repeat the same illustration

within one reading session.

Visitors should continuously discover new scenery.

---

## Final Principle

Images should create memory,

not decoration.

# Part 20
# Typography Rhythm

---

## Philosophy

Typography is architecture.

Readers should never notice fonts.

They should only notice ideas.

---

## Heading Hierarchy

H1

One per page.

H2

Major chapter.

H3

Section.

H4

Supporting topic.

Never skip heading levels.

---

## Paragraph Width

Ideal

60~75 Chinese characters.

Maximum

80.

Reading comfort always comes first.

---

## Line Height

Body

1.8

Heading

1.3

Quote

1.6

Metadata

1.5

---

## Paragraph Spacing

24px

Minimum.

Long-form reading requires breathing room.

---

## Quotes

Always isolated.

Large margins.

Different font weight.

Never place quotations inside dense paragraphs.

---

## Lists

Avoid long bullet lists.

Convert important concepts into exhibits whenever possible.

---

## Numbers

Years should use

Old Style Numerals

if supported.

Timeline labels remain subtle.

---

## Links

Links should resemble

references,

not advertisements.

Underline only on hover.

Avoid bright colors.

---

## Text Alignment

Always left aligned.

Never justify.

Centered text only in Hero

or quotations.

---

## Emphasis

Use

weight

spacing

color

before using

ALL CAPS

or

bold everywhere.

---

## Final Principle

Typography should disappear.

Ideas remain.

