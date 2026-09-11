<script lang="ts">
	// Die Bandtabelle unten kommt direkt aus dem Bandmanifest des Datenanbieters,
	// nicht aus einer abgetippten Liste — sonst beschreibt die Methodik-Seite nach
	// jeder Lieferung ein Schema, das es nicht mehr gibt.
	import manifest from "$lib/data/abschichtung.bands.json";
</script>

<svelte:head>
	<title>Methodik – Windkraft Österreich</title>
	<meta
		name="description"
		content="Wie die Windkraft-Potenzialflächen für Österreich berechnet werden: Datenquellen, Ausschlusskriterien und Vorgehen, verständlich erklärt."
	/>
</svelte:head>

<!-- Nav -->
<nav class="border-b border-slate-200 bg-white sticky top-0 z-10">
	<div class="max-w-4xl mx-auto px-4 sm:px-6 py-4 flex items-center gap-4">
		<a
			href="/"
			class="flex items-center gap-2 text-sm font-semibold transition-colors rounded focus-visible:ring-2 focus-visible:ring-blue-400"
			style="color: var(--blue-dark);"
		>
			<svg
				class="w-4 h-4"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2.5"
			>
				<path
					stroke-linecap="round"
					stroke-linejoin="round"
					d="M15 19l-7-7 7-7"
				/>
			</svg>
			Zur Karte
		</a>
		<span class="text-slate-300">|</span>
		<span class="text-sm text-slate-500">Methodik</span>
	</div>
</nav>

<div class="max-w-4xl mx-auto px-4 sm:px-6 py-12">
	<!-- Header -->
	<div class="mb-8">
		<p
			class="text-[10px] font-bold uppercase tracking-widest mb-3"
			style="color: var(--blue-sky);"
		>
			Methodik
		</p>
		<h1
			class="font-extrabold text-4xl tracking-tight mb-4"
			style="color: var(--text-dark); letter-spacing: -0.03em;"
		>
			Wie berechnen wir die Windkraft-Potenzialflächen?
		</h1>
		<p class="text-lg text-slate-600 leading-relaxed max-w-2xl">
			Diese Seite erklärt in normaler Sprache, wie die blauen Flächen auf der
			Karte entstehen: welche Daten wir verwenden, welche Flächen wir
			ausschließen und warum.
		</p>
	</div>

	<!-- Kurzfassung -->
	<div class="rounded-2xl border border-slate-200 bg-slate-50 px-5 py-4 mb-8">
		<p class="text-sm font-semibold mb-2" style="color: var(--text-dark);">
			Kurz gesagt
		</p>
		<p class="text-sm text-slate-600 leading-relaxed">
			Wir gehen von der gesamten Fläche Österreichs aus und ziehen Stück für
			Stück alles ab, wo aus rechtlichen, technischen oder ökologischen Gründen
			kein Windrad stehen darf oder soll: Siedlungen und einzelne Wohngebäude
			(mit Sicherheitsabstand), Naturschutzgebiete, Straßen, Bahnstrecken,
			Seilbahnen, Gewässer, zu steiles oder zu hoch gelegenes Gelände und
			Standorte mit zu wenig Wind. Was danach übrig bleibt und mindestens 10
			Hektar zusammenhängende Fläche bietet, zeigen wir als
			<strong>Potenzialfläche</strong>.
		</p>
	</div>

	<!-- Disclaimer -->
	<div
		class="rounded-2xl border border-amber-200 bg-amber-50 px-5 py-4 mb-10 flex gap-3"
	>
		<svg
			class="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-500"
			fill="none"
			viewBox="0 0 24 24"
			stroke="currentColor"
			stroke-width="2"
		>
			<path
				stroke-linecap="round"
				stroke-linejoin="round"
				d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
			/>
		</svg>
		<div>
			<p class="text-sm font-semibold text-amber-800 mb-1">
				Ein Grobscreening, kein Gutachten
			</p>
			<p class="text-sm text-amber-700 leading-relaxed">
				Diese Karte zeigt, wo eine Windkraftanlage grundsätzlich <em>denkbar</em
				>
				wäre — sie ersetzt keine rechtsverbindliche Standortprüfung. Themen wie Flugkorridore,
				Radar- und Richtfunkstrecken, Gasleitungen, vertragliche Abstände zwischen
				Betreibern, tatsächliche Windmessungen die tatsächliche Flächenwidmung der
				Gemeinde und eine detaillierte Umweltprüfung müssen für jedes konkrete Projekt
				gesondert untersucht werden.
			</p>
		</div>
	</div>

	<!-- Sections -->
	<div class="space-y-12">
		<!-- Siedlungsmethode -->
		<section>
			<h2 class="font-bold text-xl mb-4" style="color: var(--text-dark);">
				Wie erkennen wir Siedlungen?
			</h2>
			<p class="text-sm text-slate-700 leading-relaxed mb-3">
				Damit die Karte weiß, wo Menschen wohnen, greifen wir auf
				<strong>OpenStreetMap (OSM)</strong> zurück — eine frei zugängliche, von
				Freiwilligen gepflegte digitale Landkarte, die für Österreich sehr detailliert
				und aktuell ist. Jedes darin verzeichnete Gebäude mit einer hinterlegten
				Postadresse gilt als bewohnt. Liegen mehrere solcher Gebäude näher als 150
				Meter beieinander, fassen wir sie zu einer zusammenhängenden Siedlungsfläche
				zusammen.
			</p>
			<p class="text-sm text-slate-700 leading-relaxed mb-3">
				Damit nicht schon ein einzelnes Gehöft mitten im Wald als „Siedlung"
				durchgeht, muss diese Gebäudegruppe zusätzlich eine echte Ortschaft
				berühren — also einen Ort, der in OpenStreetMap als Stadt, Dorf, Weiler,
				Vorort oder Ortsteil eingetragen ist. Erst dann zählt die gesamte
				verbundene Fläche als Siedlungsgebiet, um das wir den gesetzlich
				vorgeschriebenen Mindestabstand ziehen (siehe Tabelle unten).
			</p>
			<p class="text-sm text-slate-500 leading-relaxed">
				Die gesamte Berechnung läuft auf einem sehr feinen Raster von 25 mal 25
				Metern — jedes einzelne Feld wird einzeln bewertet, damit die
				Abstandsgrenzen auf der Karte möglichst genau der Realität entsprechen.
			</p>
		</section>

		<!-- Abstände -->
		<section>
			<h2 class="font-bold text-xl mb-4" style="color: var(--text-dark);">
				Mindestabstände je Bundesland
			</h2>
			<p class="text-sm text-slate-700 leading-relaxed mb-3">
				Wie weit ein Windrad von der nächsten Siedlung entfernt sein muss, legt
				jedes Bundesland selbst fest. Wo verfügbar, verwenden wir dafür die
				amtliche <strong>Flächenwidmung</strong> — also die rechtlich festgelegte
				Nutzung von Grundstücken (z. B. als „Wohngebiet") — statt der oben beschriebenen
				OSM-Methode, weil sie die tatsächliche Rechtslage genauer wiedergibt. Nur
				für Wien und Burgenland gibt es keine passende amtliche Quelle; dort verwenden
				wir ersatzweise die OSM-Methode.
			</p>
			<div class="overflow-x-auto">
				<table class="w-full text-sm border-collapse">
					<caption class="sr-only"
						>Mindestabstand zu Siedlungen und Einzelgebäuden je Bundesland</caption
					>
					<thead>
						<tr class="border-b-2 border-slate-200">
							<th
								scope="col"
								class="text-left py-2 pr-6 font-semibold text-slate-700"
								>Bundesland</th
							>
							<th
								scope="col"
								class="text-right py-2 pr-6 font-semibold text-slate-700"
								>Abstand zu Siedlungen</th
							>
							<th
								scope="col"
								class="text-right py-2 font-semibold text-slate-700"
								>Abstand zu Einzelgebäuden</th
							>
						</tr>
					</thead>
					<tbody>
						{#each [["Burgenland", "1.000 m", "750 m"], ["Niederösterreich", "1.200 m", "750 m"], ["Oberösterreich", "1.000 m", "750 m"], ["Steiermark", "1.000 m", "750 m"], ["Kärnten", "1.000 m", "750 m"], ["Salzburg", "1.000 m", "750 m"], ["Tirol", "1.000 m", "750 m"], ["Vorarlberg", "1.000 m", "750 m"], ["Wien", "1.000 m", "750 m"]] as row}
							<tr
								class="border-b border-slate-100 hover:bg-slate-50 transition-colors"
							>
								<td class="py-2.5 pr-6 text-slate-800 font-medium">{row[0]}</td>
								<td class="py-2.5 pr-6 text-right text-slate-600">{row[1]}</td>
								<td class="py-2.5 text-right text-slate-600">{row[2]}</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<p class="text-xs text-slate-500 mt-3 leading-relaxed">
				<strong class="text-slate-600">Hinweis:</strong> Die Tabelle zeigt die Abstände,
				mit denen unsere Karte tatsächlich rechnet. In der Datenlieferung vom
				September 2026 wurden sie für das Burgenland von 1.200 m und für Kärnten von
				1.500 m auf jeweils 1.000 m vereinheitlicht. Ob das den landesrechtlichen
				Vorgaben entspricht, klären wir gerade mit dem Datenanbieter — in einzelnen
				Bundesländern können die gesetzlichen Mindestabstände höher liegen als hier
				gerechnet.
			</p>
			<p class="text-xs text-slate-500 mt-3 leading-relaxed">
				„Einzelgebäude" sind einzelne Wohnhäuser außerhalb von Siedlungen — etwa
				ein einzelnes Bauernhaus. Weil sie nicht Teil eines größeren
				Siedlungsgebiets sind, gilt für sie ein kleinerer Abstand als für
				Siedlungen.
			</p>
		</section>

		<!-- Neue Objektkategorien -->
		<section>
			<h2 class="font-bold text-xl mb-2" style="color: var(--text-dark);">
				Zusätzliche Sicherheitsabstände zu einzelnen Objekten
			</h2>
			<p class="text-sm text-slate-700 leading-relaxed mb-3">
				Neben Siedlungen halten wir auch zu einzelnen, empfindlichen oder
				sicherheitsrelevanten Objekten einen Mindestabstand ein.
			</p>
			<p class="text-xs text-slate-500 leading-relaxed mb-3">
				Die Kategorie „Wichtige Objekte" (250 m um Kirchen, Schlösser und ähnliche
				Landmarken) ist mit der Datenlieferung vom September 2026 entfallen. Ebenso
				entfallen ist der Abstand zu Hochspannungsfreileitungen — Freileitungen sind
				derzeit kein Ausschlusskriterium. Beides ist beim Datenanbieter angefragt.
			</p>
			<div class="space-y-3">
				{#each [{ title: "Einzelgebäude im Grünland", buffer: "750 m", note: "Einzelne Wohngebäude außerhalb von Siedlungsflächen (siehe Tabelle oben)." }, { title: "Gebäude an Seilbahnen", buffer: "50 m", note: "Gebäude im unmittelbaren Umfeld von Seilbahnanlagen, etwa Stationsgebäude." }, { title: "Nicht-Wohn-Hüllen", buffer: "25 m", note: "Gebäudehüllen ohne Wohnnutzung, etwa Betriebs- und Nebengebäude." }, { title: "Sonstige Gebäude", buffer: "25 m", note: "Alle übrigen Gebäude, die keiner anderen Kategorie zugeordnet sind." }] as cat}
					<div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
						<p
							class="text-sm font-semibold mb-1"
							style="color: var(--text-dark);"
						>
							{cat.title}
							<span class="ml-1 text-xs font-normal text-slate-400"
								>— {cat.buffer}</span
							>
						</p>
						<p class="text-xs text-slate-600">{cat.note}</p>
					</div>
				{/each}
			</div>
		</section>

		<!-- Verkehrsinfrastruktur -->
		<section>
			<h2 class="font-bold text-xl mb-4" style="color: var(--text-dark);">
				Straßen, Bahnen und Seilbahnen
			</h2>
			<p class="text-sm text-slate-700 leading-relaxed mb-4">
				Zu allen folgenden Verkehrswegen gilt ein Mindestabstand von 150 Metern
				— aus Sicherheitsgründen (Eiswurf, Rotorblattbruch) und weil dort
				ohnehin oft keine Fläche für ein Windrad frei wäre.
			</p>
			<div class="space-y-3">
				{#each [{ title: "Höherrangige Straßen", items: ["Autobahnen, Schnellstraßen sowie überregionale, regionale und lokale Hauptstraßen — inklusive ihrer Ein- und Ausfahrtsrampen.", "Straßenabschnitte in Tunneln zählen nicht dazu, da dort ohnehin kein Windrad stehen könnte."] }, { title: "Bahnstrecken", items: ["Haupt- und Regionalbahnen (Normalspur) sowie Schmalspurbahnen.", "Streckenabschnitte in Tunneln zählen nicht dazu."] }, { title: "Seilbahnen und Lifte", items: ["Anlagen für den Personentransport: Kabinenbahnen, Seilbahnen, Sessellifte sowie Schlepplifte (Anker-, Bügel- und Tellerlifte, Seilrollen) und Förderbänder.", "Reine Materialseilbahnen ohne Personentransport sind nicht mitgezählt."] }] as group}
					<div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
						<p
							class="text-sm font-semibold mb-1.5"
							style="color: var(--text-dark);"
						>
							{group.title}
							<span class="ml-1 text-xs font-normal text-slate-400"
								>— 150 m</span
							>
						</p>
						<ul class="space-y-0.5">
							{#each group.items as item}
								<li class="text-xs text-slate-600 flex gap-2">
									<span class="text-slate-300 mt-0.5">•</span>{item}
								</li>
							{/each}
						</ul>
					</div>
				{/each}
			</div>
		</section>

		<!-- Weitere Ausschlüsse -->
		<section>
			<h2 class="font-bold text-xl mb-4" style="color: var(--text-dark);">
				Naturschutz, Gelände und Wind
			</h2>
			<div class="space-y-3">
				<div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
					<p
						class="text-sm font-semibold mb-1"
						style="color: var(--text-dark);"
					>
						Naturschutzgebiete
					</p>
					<p class="text-xs text-slate-600 leading-relaxed">
						Nationalparks, Naturparks, Natura-2000-Gebiete und
						Ramsar-Feuchtgebiete sind vollständig ausgeschlossen — dort ist eine
						Windkraftanlage grundsätzlich nicht vorstellbar.
					</p>
				</div>
				<div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
					<p
						class="text-sm font-semibold mb-1"
						style="color: var(--text-dark);"
					>
						Zu steiles oder zu hoch gelegenes Gelände
					</p>
					<p class="text-xs text-slate-600 leading-relaxed">
						Hänge mit einer Neigung über 15° gelten als technisch ungeeignet.
						Ebenso ausgeschlossen sind Standorte über 2.500 m Seehöhe.
					</p>
				</div>
				<div class="rounded-xl border border-slate-100 bg-slate-50 px-4 py-3">
					<p
						class="text-sm font-semibold mb-1"
						style="color: var(--text-dark);"
					>
						Zu wenig Wind
					</p>
					<p class="text-xs text-slate-600 leading-relaxed">
						Standorte mit einer mittleren Windleistungsdichte unter 150 W/m² in
						130 m Nabenhöhe lohnen sich wirtschaftlich in aller Regel nicht und
						sind daher ausgeschlossen. Die Daten stammen aus dem European Wind
						Atlas, der die Leistungsdichte für 150 m Höhe ausweist — dort
						entspricht die Schwelle rund 160 W/m².
						Fehlen für einen Standort Winddaten, wird er sicherheitshalber
						ebenfalls ausgeschlossen. Wichtig: eine Windmessung vor Ort ist auf
						jeden Fall dennoch notwendig und liefert detailliertere Daten als
						die Modelle, die unserer Karte zu Grunde liegen.
					</p>
				</div>
			</div>
		</section>
	</div>

	<!-- Technischer Anhang -->
	<details class="mt-14 group rounded-2xl border border-slate-200 open:pb-1">
		<summary
			class="cursor-pointer list-none px-5 py-4 flex items-center gap-3 select-none focus-visible:ring-2 focus-visible:ring-blue-400 rounded-2xl"
		>
			<svg
				class="w-4 h-4 flex-shrink-0 text-slate-400 transition-transform group-open:rotate-90"
				fill="none"
				viewBox="0 0 24 24"
				stroke="currentColor"
				stroke-width="2.5"
			>
				<path stroke-linecap="round" stroke-linejoin="round" d="M9 5l7 7-7 7" />
			</svg>
			<span>
				<span
					class="text-sm font-semibold block"
					style="color: var(--text-dark);">Technischer Anhang</span
				>
				<span class="text-xs text-slate-500"
					>Für Entwickler:innen und GIS-Nutzer:innen, die mit den Rohdaten
					arbeiten möchten.</span
				>
			</span>
		</summary>
		<div class="px-5 pb-5 pt-1 space-y-3">
			<p class="text-sm text-slate-600 leading-relaxed">
				Die gesamte Berechnung basiert auf einer einzigen Rasterdatei namens
				<code class="bg-slate-100 rounded px-1.5 py-0.5 font-mono text-xs"
					>abschichtung.tif</code
				>: {manifest.band_count} Bänder (Ebenen), Datentyp {manifest.raster.dtype},
				Koordinatensystem {manifest.raster.crs} (österreichisches amtliches
				Bezugssystem), Auflösung {manifest.raster.pixel_size_m} m pro Rasterzelle.
				Jedes Band entspricht einer Zwischenstufe oder einem Teilergebnis der oben
				beschriebenen Ausschlusskriterien:
			</p>
			<div class="rounded-2xl border border-slate-200 overflow-x-auto">
				<table class="w-full text-sm">
					<caption class="sr-only"
						>Bandnummern und -namen der Quelldatei</caption
					>
					<thead>
						<tr class="bg-slate-50 border-b border-slate-200">
							<th
								scope="col"
								class="text-left px-4 py-2.5 font-semibold text-slate-600 w-16"
								>Band</th
							>
							<th
								scope="col"
								class="text-left px-4 py-2.5 font-semibold text-slate-600"
								>Name</th
							>
						</tr>
					</thead>
					<tbody>
						{#each manifest.bands as band}
							<tr
								class="border-b border-slate-100 last:border-0 hover:bg-slate-50 transition-colors"
							>
								<td
									class="px-4 py-2 text-slate-400 font-mono text-xs tabular-nums"
									>{band.index}</td
								>
								<td class="px-4 py-2 font-mono text-xs text-slate-700">
									{band.name}
									{#if band.label_de}
										<span class="font-sans text-slate-400"> — {band.label_de}</span>
									{/if}
								</td>
							</tr>
						{/each}
					</tbody>
				</table>
			</div>
			<p class="text-xs text-slate-500 leading-relaxed">
				<code class="font-mono">available_cleaned_min_10ha</code> ist die
				verfügbare Fläche nach allen Ausschlüssen, bereinigt auf
				zusammenhängende Flächen ab 10 ha — das Hauptergebnisband, aus dem die
				Potenzialflächen auf der Karte erzeugt werden.
				<code class="font-mono">official_wind_zoning</code> ist ein Referenzlayer
				(amtlich ausgewiesene Zonen in Niederösterreich, der Steiermark und Salzburg)
				und schränkt die berechneten Flächen nicht zusätzlich ein — er wird separat
				auf der Karte dargestellt.
			</p>
			<p class="text-xs text-slate-500 leading-relaxed">
				Wasserflächen (Seen, Flüsse) werden separat aus zwei Quellen
				ausgeschlossen: stehende Gewässer aus dem „Gesamtgewässernetz
				Österreich" des Umweltbundesamts, Fließgewässer-Flächen aus
				OpenStreetMap — Details siehe Repository-Dokumentation.
			</p>
		</div>
	</details>

	<!-- Footer -->
	<div class="mt-10 pt-6 border-t border-slate-200 flex items-center gap-6">
		<span class="text-xs text-slate-400">© Klimadashboard.org</span>
		<a
			href="https://klimadashboard.org/impressum"
			target="_blank"
			rel="noopener"
			class="text-xs text-slate-400 hover:text-slate-700 transition-colors"
			>Impressum</a
		>
	</div>
</div>
