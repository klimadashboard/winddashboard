import adapter from '@sveltejs/adapter-vercel';

/** @type {import('@sveltejs/kit').Config} */
const config = {
	compilerOptions: {
		// Force runes mode for the project, except for libraries. Can be removed in svelte 6.
		runes: ({ filename }) => (filename.split(/[/\\]/).includes('node_modules') ? undefined : true)
	},
	kit: {
		// Funktionen in Frankfurt statt im Vercel-Standard Washington (iad1):
		// Publikum, Regions-API und Kachelserver sitzen in Europa. Vorher ging
		// jede Gemeindeseite zweimal über den Atlantik (~0,6 s statt ~0,1 s).
		adapter: adapter({ regions: ['fra1'] })
	}
};

export default config;
