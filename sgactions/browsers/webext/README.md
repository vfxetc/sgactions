
How this works
==============

There is only one global instance of `background.js` running, and it is the only
thing that is allowed to communicate with the native messenger.

There is one instance of `main.js` per page, but it does not run in the context
of the page. It can communicate with the background, and it can inject elements
into the page.

`page/core.js` (and others) are injected into the page, and communicate with
"main" via `window.postMessage`.

Messages bettween "main" and "page" are wrapped in a simple object:

    {"sgactions": MESSAGE_HERE}.

That wrapper is added/removed when crossing the "main" boundary.

Each message must have a `src` and `dst` address. Those can be one of:

- `native` (the native messenger);
- `background` (`background.js`);
- `main` (`main.js`);
- `page` (`page/core.js`);
- an object with a `tab_id` (refering to the page) and `next` (the address
  within that page; one of `main` or `page`).
