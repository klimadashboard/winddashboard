# sv

Everything you need to build a Svelte project, powered by [`sv`](https://github.com/sveltejs/cli).

## Creating a project

If you're seeing this, you've probably already done this step. Congrats!

```sh
# create a new project
npx sv create my-app
```

To recreate this project with the same configuration:

```sh
# recreate this project
npx sv@0.15.2 create --template minimal --types ts --add tailwindcss="plugins:none" --no-install windkraft
```

## Environment variables

Copy `.env.example` to `.env` and fill in `PUBLIC_CARTO_API_KEY` — the map's
CARTO basemap requires an API key ([get one here](https://carto.com/basemaps/apikey/)).
Set the same variable in the Vercel project's environment variables for
deployed builds.

## Developing

Once you've created a project and installed dependencies with `npm install` (or `pnpm install` or `yarn`), start a development server:

```sh
npm run dev

# or start the server and open the app in a new browser tab
npm run dev -- --open
```

## Building

To create a production version of your app:

```sh
npm run build
```

You can preview the production build with `npm run preview`.

> To deploy your app, you may need to install an [adapter](https://svelte.dev/docs/kit/adapters) for your target environment.
