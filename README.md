<img src="img/Logo.gif" alt="Logo" title="Logo" align="right" width="72" height="72" />

# AI Sponge Lite

## About

AI Sponge Lite is a self-hosted Discord bot that generates parody AI Sponge audio episodes, TTS, and chats inspired by
[AI Sponge Rehydrated](https://aisponge.riskivr.com/).

There used to be a public instance of this bot with a little over 1,800 installations; however, it was shut down due to
several FakeYou device and account bans.

### Characters

SpongeBob, Patrick, Squidward, Sandy, Mr. Krabs, Plankton, Gary, Mrs. Puff, Larry, Squilliam, Karen, Narrator, 
Bubble Buddy, Bubble Bass, Perch*, Pearl*, DoodleBob, Mr. Fish, Dutchman*, King Neptune, Man Ray*, and Dirty Bubble.

Character names must be written exactly as shown above, excluding capitalization.

*Only speaks in the AI Sponge Rehydrated instance.

### Locations

SpongeBob's House, Patrick's House, Squidward's House, Sandy's Treedome, Krusty Krab, Chum Bucket, Boating School, News
Studio, Rock Bottom, and Bikini Bottom.

Locations must be written exactly as shown above, excluding capitalization.

## Usage

Only one of the following commands can be used at a time globally:

- `/episode`: Generate an audio-only episode. If an episode takes longer than 15 minutes to generate, it will be
  automatically cancelled due to Discord's interaction timeout limit.
- `/tts`: Make a character speak text. This is a shortcut to FakeYou's service. It is also the only way to access
  Squidward's and Sandy's Rehydrated voice models.
- `/chat`: Chat with a character. History is not remembered, so each message is independent. Your display name is sent
  so the character can address you.

## Installation

Installing AI Sponge Lite is only recommended for users who are comfortable with Linux and the command line.

### Discord Application and Token

1. Log in to the [Discord Developer Portal](https://discord.com/developers/applications).
2. In the top right corner, click on "New Application".
3. Name your application (e.g., "AI Sponge Lite"), click the checkbox at the bottom of the popup, and click "Create".
4. In the left sidebar, click on "Bot".
5. Scroll down slightly and click on "Reset Token". Then click "Yes, do it!" to confirm.
6. Copy the token to your clipboard or a text file. You will need it later.
7. In the left sidebar, click on "General Information".
8. Scroll down slightly and click "Copy" under "Application ID".
9. In your web browser, enter this URL, replacing `APP_ID` with your application ID:
   https://discord.com/api/oauth2/authorize?client_id=APP_ID&permissions=0&scope=bot%20applications.commands
10. Select a server to add the bot to, then click "Authorize".

Do not worry about uploading an avatar, a banner, or any emojis. When running the bot for the first time, they will
upload automatically.

### OpenAI API Key and Billing

1. Log in to the [OpenAI Platform](https://platform.openai.com/).
2. In the top right corner, click the settings icon.
3. In the left sidebar, click on "API Keys".
4. In the top right, click on "Create new secret key".
5. Name the key (e.g., "AI Sponge Lite"), select a project, and click "Create secret key".
6. Copy the key to your clipboard or a text file. You will need it later.
7. In the left sidebar, click on "Billing".
8. On the top of this page, click "Payment methods".
9. Click "Add payment method" and enter your payment information.
10. On the top of this page, click "Overview".
11. Click "Add to credit balance". $5 will keep the bot running for about six months.

### Installation Script

The following instructions are for Linux (Ubuntu, Debian, Fedora, Red Hat, and CentOS). For Windows, please install WSL,
then follow these instructions. MacOS is not supported by the installation script at the moment.

1. From this repository, download the `install.sh` script. Save it where you would like to install the bot. Do not
   download the entire repository.
2. Open a terminal and navigate to the directory where you saved the script.
3. Run the script with the command `sudo bash install.sh`.
4. When prompted, enter the Discord bot token and OpenAI API key you copied earlier. Optionally, you can enter FakeYou 
   credentials, as well as a Discord channel ID for logging.
5. Once the script is finished, you can delete the `install.sh` script.

The bot will be ready to use once its status changes to "Ready!". You may need to restart your Discord client for the
bot's avatar, banner, and commands to appear.

## Updating

If you have modified the bot's files in any way, you will need to revert those changes before updating.

1. In a terminal, navigate to the `AISpongeLite` directory the bot was installed to.
2. Run the command `sudo bash install.sh`.

The bot will be ready to use once its status changes to "Ready!".

## Demonstration

![Episode](img/episode.png)
![TTS](img/tts.png)
![Chat](img/chat.png)