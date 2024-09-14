<img src="img/Logo.gif" alt="Logo" title="Logo" align="right" width="72" height="72" />

# AI Sponge Lite

## About

AI Sponge Lite (sometimes called "Lite") is a Discord bot that generates audio-only AI Sponge episodes with transcripts
inspired by AI Sponge Rehydrated (sometimes called "Rehydrated").

### Characters

The available characters are SpongeBob, Patrick, Squidward, Loudward, Gary, Sandy, Mr. Krabs, Plankton, Karen,
Mrs. Puff, Squilliam, Larry, Bubble Bass, Bubble Buddy, and the French Narrator. Some characters will sound different 
from Rehydrated due to them using private models.

### Background Music

The available background music is the SpongeBob SquarePants closing theme, The Tip Top Polka, The Rake Hornpipe, and
Seaweed. One of these is chosen at random per episode. There is also a rare chance that Sneaky Snitch or the Better Call
Saul opening will be chosen as a callback to the original AI Sponge.

### Sound Effects

The available sound effects are steel sting, boowomp, vibe link (b), disgusting fog horn, "My leg!", "Oh brother this 
guy stinks!", "You what?", and the dolphin censor sound. One of these is chosen at random to play at a random point per 
episode. The beginning of every episode begins with the bubbles transition sound.

### Random Events

The available random events are speech cutoffs and loud events. Both of these can happen in an episode any number of
times. Loud events also occur every time Loudward speaks. Cutoffs also occur anytime a line ends with a hyphen.

### Strokes

Lite supports all strokes, which are when FakeYou glitches out and generates abnormal audio. The volumes of characters
are normalized, so strokes will not be full volume (unless a loud event occurs).

## Usage

- `/generate`: Generate an episode. Only one episode can be generated at a time globally. There is a 5-minute cooldown
  upon successful generation. Generation may take around 15 minutes.
- `/status`: Check if an episode can be generated. This will show if the bot is busy, if you are on cooldown,
  or if the bot is idle.

## Installation

Click the link in the "About" section of the repository, then click "Add App" on the next page. After that, follow the
instructions in the popup.

## Troubleshooting

- If you encounter the error "Missing required permissions.", make sure the bot has the following permissions: View
  Channels, Embed Links, Attach Files, and Read Message History.
- If you encounter the error "Failed to generate episode.", try using the generate command again. If it happens right
  after generation jumps from 0%, try changing the wording of your topic.

## Demonstration

![Output](img/output.png)
