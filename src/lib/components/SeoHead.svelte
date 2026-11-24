<script lang="ts">
	import { page } from "$app/stores";

	/**
	 * Zentrale Stelle für Titel, Beschreibung, Canonical und Social-Karten.
	 *
	 * Die Basis-URL kommt aus der Request-Origin statt aus einer Konstanten —
	 * damit stimmen Canonical und Vorschaubild auf der Produktionsdomain, in
	 * Vercel-Preview-Deployments und lokal, ohne dass irgendwo eine Domain
	 * hartkodiert ist, die beim Umzug still falsch wird.
	 */
	let {
		title,
		description,
		/** Ohne Angabe die aktuelle URL ohne Query — Suchmaschinen sollen
		 *  ?v=1-Varianten nicht als eigene Seiten führen. */
		canonicalPath = undefined,
		// ?v= erzwingt bei Facebook, LinkedIn & Co. einen neuen Abruf, wenn
		// sich das Bild ändert — sie halten Vorschaubilder sonst wochenlang.
		image = "/og-image.jpg?v=2",
		imageAlt = "Österreich-Karte mit den Flächen, auf denen Windräder möglich sind: 4,2 % der Landesfläche",
		type = "website",
	}: {
		title: string;
		description: string;
		canonicalPath?: string;
		image?: string;
		imageAlt?: string;
		type?: string;
	} = $props();

	const origin = $derived($page.url.origin);
	const canonical = $derived(origin + (canonicalPath ?? $page.url.pathname));
	const imageUrl = $derived(origin + image);
</script>

<svelte:head>
	<title>{title}</title>
	<meta name="description" content={description} />
	<link rel="canonical" href={canonical} />

	<meta property="og:type" content={type} />
	<meta property="og:title" content={title} />
	<meta property="og:description" content={description} />
	<meta property="og:url" content={canonical} />
	<meta property="og:image" content={imageUrl} />
	<meta property="og:image:type" content="image/jpeg" />
	<meta property="og:image:alt" content={imageAlt} />
	<meta property="og:image:width" content="1200" />
	<meta property="og:image:height" content="630" />
	<meta property="og:locale" content="de_AT" />
	<meta property="og:site_name" content="winddashboard.at" />

	<meta name="twitter:card" content="summary_large_image" />
	<meta name="twitter:title" content={title} />
	<meta name="twitter:description" content={description} />
	<meta name="twitter:image" content={imageUrl} />
	<meta name="twitter:image:alt" content={imageAlt} />
</svelte:head>
