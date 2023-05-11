Hobune needs a few changes made and I think it might be best to create a "v2" for this.

Strikethrough means already implemented.

- ~~Recreate the design in a more pure way~~
  - ~~Look and feel should stay close to what it is now~~
  - Dark theme support
  - ~~Semantic/Fomantic UI shouldn't be used as it's bloat (both in terms of performance and )~~
  - ~~No JS should be used except where functionally necessary~~
- Smarter ways of handling pages with a lot of content
  - (optional) Client-side DOM lazy-load?
- ~~Sorting/search options on pages~~
  - ~~By name, date, views; filter by removed/unlisted~~
  - Search by video/channel title *and* ID
- ~~Better channel ID and name handling~~
  - ~~Make sure channel ID vs /user/ doesn't get separated~~
  - ~~Store all historic channel names found so they can be used in search~~
- ~~Separate app into multiple components/files for better modularity and plugins~~
- ~~Make it work on Windows by default~~
- Dedupe videos by default
- Comments page should show comments count (both top-level and all)
  ~~- Link back to YouTube links wherever possible~~
- Make it easier to download everything, eg provide a wget command (maybe we could even download and generate a zip in JS for smaller channels?)
- Support generating comments even if video itself isn't present
- Cache folder listings (so we don't like /other a hundred thousand times)
- Extract metadata gathering from info.json into a separate module so it can easily be extended for fallbacks
- Single video/channel mode
- Video length
