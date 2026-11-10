# About this profile

Animated SVG cards inspired by [Avi Vashishta's profile walkthrough](https://www.avivashishta.com/blog/github-profile-readme-animated-svg-cards). Original layout and artwork for Nikita Lomovtsev.

The README uses GitHub-compatible `<picture>` elements to select light or dark SVG cards according to the viewer's color-scheme preference. On narrow screens the hero switches to a more legible composition. Projects come first; navigation links lead to the toolkit and activity sections. All project cards link to public repositories.

Edit `profile.json` to change the name, introduction, featured public repositories and linked tiles. The renderer uses Python's standard library; the fetcher uses GitHub CLI (`gh`), already installed on GitHub's Ubuntu runners. No Python packages or external card services are needed. The Instrument Serif font is embedded in each SVG, with its SIL Open Font License in `fonts/`.

GitHub Actions refreshes public contribution data and repository metadata daily at 05:23 UTC (08:23 Moscow), and after configuration changes. GitHub may delay scheduled runs or disable schedules in inactive public repositories after 60 days. Use **Actions → Refresh profile cards → Run workflow** to refresh manually. Only the built-in repository token is required; no personal token needs to be saved.

## Local refresh

```sh
GH_TOKEN="$(gh auth token)" python3 scripts/update_data.py
python3 scripts/render_cards.py
```

The fetcher replaces the data file only after a successful response. If fetching fails, the existing published cards remain available and the workflow reports a failure. Repository metadata is limited to public repositories. Contributions use GitHub's reported calendar and may reflect private-contribution counts if the profile owner enables those publicly; no private project names or contents are included.

## Static preview

```sh
STATIC=1 CARD_OUTPUT=/tmp/profile-static python3 scripts/render_cards.py
```

Static output is kept separate from the animated cards. Animations also stop when the viewer requests reduced motion. README links and image descriptions remain available without animation.

The monthly chart shows twelve calendar months, including the partial current month. Streaks and activity figures cover the displayed contribution calendar. The current streak allows an unfinished current day. GitHub's own attribution and timezone rules determine the underlying contribution dates.
