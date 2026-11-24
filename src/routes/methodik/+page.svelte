<script lang="ts">
	// Methodik nach der Kurzfassung „Methodik_Kurzfassung_Website“ (November 2026),
	// die die frühere, ausführliche Seite mit Band-Tabelle vollständig ersetzt.
	// Abweichungen vom Dokument, abgestimmt am 18.11.2026:
	//   - Schutzgebiete: 15.435 km² (exclusion_nature der Lieferung vom
	//     19.11.2026, 1.543.458 ha, 18,4 %). Ramsar-Gebiete zählen dort nicht
	//     mehr; das Dokument nannte 15.670 km², die Vorlieferung 15.683 km².
	//   - Freileitungen: 136 m gelten auch für 400 kV (Manifest).
	//   - Zitat und Quellen am Ende ergänzt (Datensatz J. Hurt, Statistik Austria,
	//     Energy-Charts, Hintergrundkarte).
	// Burgenland mit 1.200 m: seit der Lieferung vom 19.11.2026 rechnet auch die
	// Karte so (Default-Variante „Länderregel“).
	import SeoHead from "$lib/components/SeoHead.svelte";
	import SiteFooter from "$lib/components/SiteFooter.svelte";

	type Link = { label: string; href: string };
	type Row = { kriterium: string; regel: string; daten: Link[]; datenText?: string };
	type Group = { name: string; color: string; rows: Row[] };

	const OSM: Link = { label: "OpenStreetMap", href: "https://www.openstreetmap.org/copyright" };
	const DGM: Link = {
		label: "Geländemodell BEV (DGM 25 m)",
		href: "https://data.bev.gv.at/download/DGM/Hoehenraster/DGM_R25.tif",
	};
	const NOE_SEKROP =
		"https://www.raumordnung-noe.at/land/ueberoertliche-raumordnung/raumordnungsprogramme/raumordnungsprogramme-fuer-sachbereiche/sektorales-raumordnungsprogramm-ueber-windkraftnutzung-in-noe-1";

	const WIDMUNG: Link[] = [
		{ label: "Burgenland", href: "https://www.burgenland.at/service/open-government-data/bestandsliste/detail/flaechenwidmung-burgenland-widmungsflaechen/" },
		{ label: "Kärnten", href: "https://kagis.ktn.gv.at/Geodaten/Open-Government-Data" },
		{ label: "Niederösterreich", href: "https://www.noe.gv.at/noe/OGD_Detailseite.html?id=81a23612-9823-4a61-95cb-09aea8242db8" },
		{ label: "Oberösterreich", href: "https://www.data.gv.at/katalog/dataset/land-ooe_flachenwidmung-widmungen-flachen-oberosterreich" },
		{ label: "Salzburg", href: "https://service.salzburg.gv.at/ogd/client/showDetail/d7b4c0c9-3407-4dba-9e15-9b60ea7d00f7" },
		{ label: "Steiermark", href: "https://data.steiermark.at/cms/beitrag/12762373/97428847/" },
		{ label: "Tirol", href: "https://www.data.gv.at/katalog/dataset/AE90DD7E-79C9-48AA-B685-732B357E9246" },
		{ label: "Vorarlberg", href: "https://vogis.cnv.at/geonetwork/srv/api/records/85bd045b-8857-4388-bc07-0fccd5a29eb1" },
		{ label: "Wien", href: "https://www.wien.gv.at/stadtentwicklung/flaechenwidmung/geodaten.html" },
	];

	const GROUPS: Group[] = [
		{
			name: "Mensch",
			color: "#f97316",
			rows: [
				{
					kriterium: "Siedlungen",
					regel: "1.000 m Abstand, in Niederösterreich und im Burgenland 1.200 m",
					datenText: "Flächenwidmung der Länder:",
					daten: WIDMUNG,
				},
				{
					kriterium: "Häuser im Grünen",
					regel: "750 m Abstand",
					datenText: "Flächenwidmung,",
					daten: [
						{ label: "Kataster", href: "https://data.bev.gv.at/geonetwork/srv/api/records/279a32e9-c001-4508-914c-5e00952d6156" },
						{ label: "Adressregister", href: "https://www.bev.gv.at/Services/Produkte/Adressregister/Oesterreichisches-Adressregister.html" },
						{ label: "Mindestabstandszonen Niederösterreich", href: NOE_SEKROP },
					],
				},
				{
					kriterium: "Übrige Gebäude",
					regel:
						"Um alle anderen Gebäude halten wir 25 m Abstand ein – das entspricht praktisch ihrer Grundfläche. Gebäude, die höchstens 100 m neben einer Personenseilbahn liegen, gelten als Seilbahnstation und bekommen 50 m.",
					datenText: "Kataster,",
					daten: [OSM],
				},
				{
					kriterium: "Verkehr",
					regel:
						"150 m Abstand auf beiden Seiten von Autobahnen und Schnellstraßen, Bundes- und Landesstraßen, Hauptbahnen und Personenseilbahnen (Gondel-, Kabinen- und Pendelbahnen, Sessellifte und Kombibahnen). Abschnitte in Tunneln zählen nicht.",
					daten: [OSM],
				},
				{
					kriterium: "Militär",
					regel:
						"Militärisch genutzte Flächen: Truppenübungs- und Schießplätze, Gefahrenzonen, Kasernen, Militärflugplätze, Munitionsanstalten und sonstige Militärstandorte. Den Großteil machen die Truppenübungsplätze Allentsteig, Lizum/Walchen, Bruckneudorf, Großmittel, Hochfilzen und Seetaler Alpe aus.",
					daten: [OSM],
				},
				{
					kriterium: "Luftfahrt",
					regel:
						"Flughafenareal der sechs Verkehrsflughäfen Wien-Schwechat, Graz, Linz, Salzburg, Innsbruck und Klagenfurt. Dazu kommen an jedem Pistenende An- und Abflugkorridore von 5 km Länge und ±15° um die verlängerte Pistenachse. Kleinere Flugplätze sind nicht berücksichtigt.",
					daten: [OSM],
				},
				{
					kriterium: "Freileitungen",
					regel: "116 m Abstand zu Freileitungen mit 110 kV, 136 m zu Freileitungen mit 220, 380 und 400 kV",
					daten: [OSM],
				},
			],
		},
		{
			name: "Natur",
			color: "#16a34a",
			rows: [
				{
					kriterium: "Schutzgebiete",
					regel:
						"Nationalparks, Naturschutzgebiete, Europaschutzgebiete (Natura 2000), Geschützte Landschaftsteile, Sonstige Schutzgebiete (nur verordnete Kategorien) und Naturdenkmäler. Landschaftsschutzgebiete zählen nicht dazu.",
					daten: [{ label: "Umweltbundesamt", href: "https://www.umweltbundesamt.at/umweltthemen/naturschutz/schutzgebiete" }],
				},
			],
		},
		{
			name: "Geografie",
			color: "#78716c",
			rows: [
				{ kriterium: "Hangneigung", regel: "steiler als 15°", daten: [DGM] },
				{ kriterium: "Seehöhe", regel: "über 2.500 m", daten: [DGM] },
				{
					kriterium: "Wind",
					regel: "unter 150 W/m² in 130 m Höhe",
					daten: [{ label: "Global Wind Atlas", href: "https://globalwindatlas.info" }],
				},
				{ kriterium: "Gewässer", regel: "Seen, Stauseen und Flüsse ab 1 ha", daten: [OSM] },
			],
		},
	];

	const ZONEN: Link[] = [
		{ label: "Niederösterreich", href: NOE_SEKROP },
		{ label: "Burgenland*", href: "https://www.burgenland.at/service/open-government-data/bestandsliste/detail/windkraftanlagen-eignungszonen-burgenland/" },
		{ label: "Steiermark", href: "https://www.landesentwicklung.steiermark.at/cms/beitrag/12755541/154267170/" },
		{ label: "Kärnten", href: "https://www.ris.bka.gv.at/Dokumente/LgblAuth/LGBLA_KA_20260220_11/Anlage_Anlage_zu___7c_Abs._2.pdf" },
		{ label: "Salzburg", href: "https://www.salzburg.gv.at/fileadmin/Dateien/Bauen-Wohnen/Raumplanung/Raumordnung_Publikationen/260928V2_Landesentwicklungsprogramm_2026_Online.pdf" },
	];

	const DATASET_DOI = "https://doi.org/10.5281/zenodo.24267882";
</script>

<SeoHead
	title="Methodik: Wie wir Windkraft-Potenzialflächen berechnen"
	description="Welche Daten wir verwenden, welche Flächen wir ausschließen und wie die Windkraft-Potenzialkarte für Österreich entsteht — Abstände, Schutzgebiete, Gelände und Wind."
/>

<!-- Nav -->
<nav class="border-b border-slate-200 bg-white sticky top-0 z-10">
	<div class="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
		<a
			href="/"
			class="flex items-center gap-2 text-sm font-semibold transition-colors rounded focus-visible:ring-2 focus-visible:ring-blue-400"
			style="color: var(--blue-dark);"
		>
			<svg class="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="2.5" aria-hidden="true">
				<path stroke-linecap="round" stroke-linejoin="round" d="M15 19l-7-7 7-7" />
			</svg>
			Zur Karte
		</a>
		<span class="text-slate-300" aria-hidden="true">|</span>
		<span class="text-sm text-slate-500">Methodik</span>
	</div>
</nav>

{#snippet citation()}
	<blockquote class="border-l-2 border-slate-300 pl-4 text-base text-slate-700 leading-relaxed">
		J. Hurt, „Wind power exclusion and suitability areas for Austria on a 25 m grid (Abschichtung
		Windkraft Österreich)“,
		<a href={DATASET_DOI} target="_blank" rel="noopener" class="underline underline-offset-2 break-all hover:text-slate-900"
			>{DATASET_DOI}</a
		>
	</blockquote>
{/snippet}

{#snippet links(items: Link[])}
	{#each items as link, i}<a
			href={link.href}
			target="_blank"
			rel="noopener"
			class="underline decoration-slate-300 underline-offset-2 hover:text-slate-900 hover:decoration-slate-500"
			>{link.label}</a
		>{i < items.length - 1 ? ", " : ""}{/each}
{/snippet}

<div class="max-w-4xl mx-auto px-4 sm:px-6 py-12">
	<!-- Header -->
	<div class="mb-8">
		<p class="text-xs font-bold uppercase tracking-widest mb-3" style="color: var(--blue-sky-ink);">
			Methodik
		</p>
		<h1
			class="font-extrabold text-3xl sm:text-4xl tracking-tight mb-4"
			style="color: var(--text-dark); letter-spacing: -0.03em; text-wrap: balance;"
		>
			Wie berechnen wir die Windkraft-Potenzialflächen?
		</h1>
		<p class="text-lg text-slate-600 leading-relaxed max-w-2xl">
			Diese Seite erklärt, welche Daten wir verwenden, wie wir die Potenzialflächen berechnen und
			was die Karte zeigt.
		</p>
		<p class="text-sm text-slate-600 mt-3">Letztes Update: November 2026</p>
	</div>

	<!--
		Früher vier verschieden gestaltete Kästen untereinander (grau, Zitat,
		gelbe Warnung mit Symbol). Jetzt normale Abschnitte in derselben
		Typografie wie der Rest der Seite; der Hinweis zum Grobscreening steht als
		eigener Abschnitt direkt danach und verliert dadurch nichts an Gewicht.
	-->
	<section class="mb-12 max-w-2xl">
		<h2 class="font-bold text-xl mb-3" style="color: var(--text-dark);">Kurz gesagt</h2>
		<p class="text-base text-slate-700 leading-relaxed">
			Wir legen über ganz Österreich alle Flächen, auf denen nach einheitlichen Kriterien kein
			Windrad stehen kann: Abstände zu Siedlungen und Gebäuden, Verkehrswege, Militärgebiete und
			Flughäfen, Schutzgebiete, zu steiles oder zu hoch gelegenes Gelände, Gewässer und Standorte
			mit zu wenig Wind. Was danach übrig bleibt und zusammenhängend mindestens 10&nbsp;Hektar groß
			ist, zeigen wir als <strong>Potenzialfläche</strong>.
		</p>
		<p class="text-base text-slate-700 leading-relaxed mt-4">
			<strong>Datengrundlage:</strong> J. Hurt, „Wind power exclusion and suitability areas for
			Austria on a 25 m grid (Abschichtung Windkraft Österreich)“,
			<a href={DATASET_DOI} target="_blank" rel="noopener" class="underline underline-offset-2 break-all hover:text-slate-900"
				>{DATASET_DOI}</a
			>
		</p>
	</section>

	<section class="mb-14 max-w-2xl">
		<h2 class="font-bold text-xl mb-3" style="color: var(--text-dark);">Ein Grobscreening, kein Gutachten</h2>
		<div class="space-y-3">
			<p class="text-base text-slate-700 leading-relaxed">
			Die Karte zeigt, wo ein Windrad grundsätzlich denkbar wäre. Sie ersetzt keine
			Standortprüfung und ist keine Grundlage für eine Genehmigung. Für jedes konkrete Projekt
			müssen Naturschutz, Schall und Schattenwurf einzeln geprüft werden. Die Karte gibt außerdem
			keine Auskunft über einen möglichen Netzanschluss oder die Verfügbarkeit der Grundstücke.
			Für jedes Projekt ist zudem eine eigene Windmessung vor Ort nötig, um die
			Wirtschaftlichkeit zu prüfen.
			</p>
			<p class="text-base text-slate-700 leading-relaxed">
			Wir haben ausschließlich mit öffentlich zugänglichen Daten gearbeitet und zur Vereinfachung
			einheitliche Annahmen getroffen. Die Karte kann daher Flächen enthalten, die wir als
			Potenzialfläche zeigen, bei einer genaueren Prüfung jedoch wegfallen. Umgekehrt können
			Flächen, die wir nicht als Potenzialfläche ausweisen, sich bei genauer Prüfung als geeignet
			herausstellen.
			</p>
		</div>
	</section>

	<div class="space-y-14">
		<!-- Drei Gruppen -->
		<section>
			<h2 class="font-bold text-2xl mb-2" style="color: var(--text-dark);">Drei Gruppen von Ausschlüssen</h2>
			<p class="text-base text-slate-600 leading-relaxed mb-6 max-w-2xl">
				Jede Fläche, auf die eines der folgenden Kriterien zutrifft, ist ausgeschlossen.
			</p>
			<!--
				Keine klassische Tabelle: vier Spalten mit langen Regeltexten und
				Linklisten sind auf dem Telefon nicht lesbar. Stattdessen je Kriterium
				eine Zeile, die ab sm in drei Spalten (Kriterium | Regel | Daten) läuft
				und darunter untereinander steht.
			-->
			<div class="space-y-8">
				{#each GROUPS as group}
					<div>
						<div class="flex items-center gap-2 mb-2">
							<span class="w-3 h-3 rounded-sm" style="background:{group.color};" aria-hidden="true"></span>
							<h3 class="text-base font-bold" style="color: var(--text-dark);">
								{group.name}
							</h3>
						</div>
						<div class="hidden sm:grid grid-cols-[9rem_1fr_13rem] gap-x-6 text-xs uppercase tracking-wide text-slate-600 font-semibold pb-1.5 border-b border-slate-300">
							<span>Kriterium</span><span>Regel</span><span>Daten</span>
						</div>
						<dl>
							{#each group.rows as row}
								<div class="grid sm:grid-cols-[9rem_1fr_13rem] gap-x-6 gap-y-1 py-3 border-b border-slate-200">
									<dt class="font-semibold text-slate-800 text-sm">{row.kriterium}</dt>
									<dd class="text-sm text-slate-700 leading-relaxed min-w-0">{row.regel}</dd>
									<dd class="text-sm text-slate-600 leading-relaxed min-w-0">
										<span class="sm:hidden font-semibold text-slate-700">Daten: </span>
										{#if row.datenText}{row.datenText}{" "}{/if}{@render links(row.daten)}
									</dd>
								</div>
							{/each}
						</dl>
					</div>
				{/each}
			</div>
		</section>

		<!-- Mensch -->
		<section>
			<h2 class="font-bold text-2xl mb-6" style="color: var(--text-dark);">
				Mensch: Abstände zu Siedlungen, Gebäuden und Infrastruktur
			</h2>
			<h3 class="font-semibold text-lg mb-2" style="color: var(--text-dark);">Wie erkennen wir Siedlungen?</h3>
			<p class="text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				Als Siedlung zählt, was als Wohn-, Misch-, Kern- oder Dorfgebiet gewidmet ist. Industrie-,
				Betriebs- und Gewerbegebiete zählen nicht dazu. Die Daten entnehmen wir der
				<strong>Flächenwidmung</strong>, also dem amtlichen Plan, in dem jede Gemeinde festlegt,
				wofür ein Grundstück genutzt werden darf.
			</p>
			<p class="text-base text-slate-700 leading-relaxed mb-8 max-w-2xl">
				Die Widmungspläne liegen uns für alle neun Bundesländer vor. Die Länder benennen ihre
				Widmungen unterschiedlich, deshalb haben wir für jedes Land festgelegt, welche Widmungen als
				Siedlung gelten. Für Wien ist nur der vereinfachte Widmungsplan offen verfügbar.
			</p>

			<h3 class="font-semibold text-lg mb-2" style="color: var(--text-dark);">Was sind Häuser im Grünen?</h3>
			<p class="text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				Um bewohnte Häuser außerhalb des Baulands gilt ein Abstand von 750&nbsp;m. Dazu zählen zwei
				Arten von Flächen:
			</p>
			<ul class="list-disc pl-5 space-y-2 text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				<li>
					<strong>Sonderwidmungen außerhalb des Baulands</strong>, etwa Hofstellen, Campingplätze,
					Kleingärten, Golfplätze sowie Ferienhaus- und Tourismusgebiete. Welche Widmungen das sind,
					ist je Land verschieden.
				</li>
				<li>
					<strong>Streusiedlungen</strong>, die in keiner Widmung stehen. Wir erkennen sie aus dem
					Kataster und dem Adressregister: Bebaute Flächen, die höchstens rund 200&nbsp;m
					auseinanderliegen, bilden eine Gruppe. Haben mindestens fünf davon eine Hausnummer im
					Umkreis von 100&nbsp;m, gilt die Gruppe als Streusiedlung.
				</li>
			</ul>
			<p class="text-base text-slate-700 leading-relaxed max-w-2xl">
				In Niederösterreich gelten stattdessen die
				<a href={NOE_SEKROP} target="_blank" rel="noopener" class="underline underline-offset-2 hover:text-slate-900"
					>amtlichen Mindestabstandszonen des Landes</a
				>.
			</p>
		</section>

		<!-- Natur -->
		<section>
			<h2 class="font-bold text-2xl mb-4" style="color: var(--text-dark);">Natur: Schutzgebiete</h2>
			<p class="text-base text-slate-700 leading-relaxed max-w-2xl">
				Ausgeschlossen sind Gebiete, die nach dem Naturschutzrecht der Länder per Verordnung oder
				Bescheid geschützt sind. Die Daten stammen ausschließlich vom
				<a
					href="https://www.umweltbundesamt.at/umweltthemen/naturschutz/schutzgebiete"
					target="_blank"
					rel="noopener"
					class="underline underline-offset-2 hover:text-slate-900">Umweltbundesamt</a
				>. Zusammen sind das 15.435&nbsp;km², also 18,4&nbsp;% der Fläche Österreichs.
			</p>
		</section>

		<!-- Geografie -->
		<section>
			<h2 class="font-bold text-2xl mb-6" style="color: var(--text-dark);">Geografie: Gelände, Wind und Gewässer</h2>

			<h3 class="font-semibold text-lg mb-2" style="color: var(--text-dark);">Zu steiles oder zu hoch gelegenes Gelände</h3>
			<p class="text-base text-slate-700 leading-relaxed mb-8 max-w-2xl">
				Flächen mit einer Hangneigung über 15° gelten als technisch ungeeignet. Die Neigung berechnen
				wir über eine Fläche von rund 300&nbsp;×&nbsp;300&nbsp;m, damit einzelne kleine Böschungen nicht
				ins Gewicht fallen. Ebenso ausgeschlossen sind Standorte über 2.500&nbsp;m Seehöhe.
			</p>

			<h3 class="font-semibold text-lg mb-2" style="color: var(--text-dark);">Zu wenig Wind</h3>
			<p class="text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				Standorte mit einer mittleren Windleistungsdichte unter 150&nbsp;W/m² in 130&nbsp;m Nabenhöhe
				lohnen sich wirtschaftlich in aller Regel nicht und sind daher ausgeschlossen. Die Daten
				stammen aus dem Global Wind Atlas der Technischen Universität Dänemark und der Weltbank. Er
				weist die Leistungsdichte für 150&nbsp;m Höhe aus, dort entspricht die Schwelle rund
				160&nbsp;W/m². Fehlen für einen Standort Winddaten, wird er ebenfalls ausgeschlossen.
			</p>
			<p class="text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				Eine Windmessung vor Ort ist trotzdem immer notwendig. Sie dauert in der Regel ein Jahr und
				liefert genauere Daten als das Modell, das unserer Karte zugrunde liegt.
			</p>
			<p class="text-sm text-slate-600 leading-relaxed mb-8 max-w-2xl">
				Quelle: Davis, N. N., Badger, J., Hahmann, A. N. et al. (2023): The Global Wind Atlas: A
				high-resolution dataset of climatologies and associated web-based application. Bulletin of
				the American Meteorological Society 104(8), E1507–E1525.
				<a href="https://doi.org/10.1175/BAMS-D-21-0075.1" target="_blank" rel="noopener" class="underline underline-offset-2"
					>doi:10.1175/BAMS-D-21-0075.1</a
				>. Daten: Global Wind Atlas, Leistungsdichte in 150&nbsp;m Höhe,
				<a href="https://globalwindatlas.info" target="_blank" rel="noopener" class="underline underline-offset-2"
					>globalwindatlas.info</a
				>.
			</p>

			<h3 class="font-semibold text-lg mb-2" style="color: var(--text-dark);">Gewässer</h3>
			<p class="text-base text-slate-700 leading-relaxed max-w-2xl">
				Seen, Stauseen und Flüsse sind ausgeschlossen, sobald sie zusammenhängend mindestens
				1&nbsp;ha groß sind.
			</p>
		</section>

		<!-- Weitere Hinweise -->
		<section>
			<h2 class="font-bold text-2xl mb-6" style="color: var(--text-dark);">Weitere methodische Hinweise</h2>
			<dl class="divide-y divide-slate-200 border-y border-slate-200">
				<div class="grid sm:grid-cols-[13rem_1fr] gap-x-6 gap-y-1 py-4">
					<dt class="font-semibold text-slate-800 text-sm">Windkraftzonen der Bundesländer</dt>
					<dd class="text-sm text-slate-700 leading-relaxed min-w-0 space-y-2">
						<p>{@render links(ZONEN)}</p>
						<p>
							In Oberösterreich, Vorarlberg, Tirol und Wien gibt es keine vom Land ausgewiesenen
							Windkraft-Zonen.
						</p>
						<p class="text-sm text-slate-600">
							*Das Land Burgenland veröffentlicht nur die aktuellen Eignungszonen, nicht die älteren
							Zonen, in denen bereits Windräder stehen. Deshalb liegen auf der Karte viele
							burgenländische Windräder scheinbar außerhalb der Zonen. Um solche bestehenden Windparks
							haben wir eine eigene (türkise) Fläche berechnet. Sie sind kein Rechtsakt, sondern
							dienen nur zur Orientierung.
						</p>
					</dd>
				</div>
				<div class="grid sm:grid-cols-[13rem_1fr] gap-x-6 gap-y-1 py-4">
					<dt class="font-semibold text-slate-800 text-sm">Bestehende Windräder</dt>
					<dd class="text-sm text-slate-700 leading-relaxed">
						<a href="https://www.wind.at/aktuelles/windrad-karte" target="_blank" rel="noopener" class="underline underline-offset-2 hover:text-slate-900"
							>Windkraft Österreich, Windrad-Karte</a
						>, Stand: Jänner 2026
					</dd>
				</div>
				<div class="grid sm:grid-cols-[13rem_1fr] gap-x-6 gap-y-1 py-4">
					<dt class="font-semibold text-slate-800 text-sm">OpenStreetMap</dt>
					<dd class="text-sm text-slate-700 leading-relaxed">
						OpenStreetMap-Mitwirkende (2026): OpenStreetMap-Extrakt Österreich, bereitgestellt von der
						<a href="https://download.geofabrik.de/europe/austria.html" target="_blank" rel="noopener" class="underline underline-offset-2 hover:text-slate-900"
							>Geofabrik GmbH</a
						>. Lizenz ODbL 1.0. Datenstand 12.11.2026.
					</dd>
				</div>
			</dl>
		</section>

		<!-- Zitat & Quellen -->
		<section>
			<h2 class="font-bold text-2xl mb-4" style="color: var(--text-dark);">Zitat und Quellen</h2>
			<p class="text-base text-slate-700 leading-relaxed mb-3 max-w-2xl">
				Die Ausschluss- und Potenzialflächen beruhen auf diesem Datensatz. Bitte zitiere ihn so:
			</p>
			<div class="mb-8 max-w-2xl">{@render citation()}</div>
			<h3 class="font-semibold text-lg mb-3" style="color: var(--text-dark);">Weitere Quellen</h3>
			<ul class="space-y-2 text-sm text-slate-700 leading-relaxed max-w-2xl">
				<li>
					<strong>Gemeindegrenzen</strong> für die Gemeindeseiten:
					<a href="https://data.statistik.gv.at" target="_blank" rel="noopener" class="underline underline-offset-2 hover:text-slate-900"
						>Statistik Austria</a
					>, Stand 1.1.2026, Lizenz CC BY 4.0
				</li>
				<li>
					<strong>Fläche Österreichs</strong> (8.388.387&nbsp;ha): Bundesamt für Eich- und
					Vermessungswesen / Statistik Austria, „Fläche und Benützungsarten“, Stand 1.1.2025
				</li>
				<li>
					<strong>Stromerzeugung aus Windkraft:</strong>
					<a href="https://www.energy-charts.info/charts/energy/chart.htm?l=de&c=AT&interval=year" target="_blank" rel="noopener" class="underline underline-offset-2 hover:text-slate-900"
						>Energy-Charts</a
					>, Fraunhofer ISE
				</li>
				<li>
					<strong>Hintergrundkarte:</strong> © OpenStreetMap-Mitwirkende, © CARTO
				</li>
			</ul>
		</section>
	</div>

	<!-- Footer -->
	<div class="mt-14 pt-6 border-t border-slate-200">
		<SiteFooter showMethodikLink={false} />
	</div>
</div>
