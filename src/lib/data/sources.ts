export interface Source {
	id: number;
	citation: string;
	url?: string;
}

export const sources: Source[] = [
	{
		id: 1,
		citation: '„Energy Charts“. Zugegriffen: 29. April 2026.',
		url: 'https://api.energy-charts.info/public_power?country=at&start=2020-01-01&end=2025-12-31'
	},
	{
		id: 2,
		citation:
			'R. A. Rogowsky, K. Laney-Cummings, A. S. David, M. Reed, und M. Anderson, „Industry and Trade Summary 2009“, United States International Trade Commission.'
	},
	{
		id: 3,
		citation: '„V172-7.2 MW™“. Zugegriffen: 22. April 2026.',
		url: 'https://www.vestas.com/en/energy-solutions/onshore-wind-turbines/enventus-platform/V172-7-2-MW'
	},
	{
		id: 4,
		citation:
			'J. Hengstler, M. Russ, A. Stoffregen, A. Hendrich, D. M. Held, und A.-K. Briem, „Aktualisierung und Bewertung der Ökobilanzen von Windenergie- und Photovoltaikanlagen unter Berücksichtigung aktueller Technologieentwicklungen“.'
	},
	{
		id: 5,
		citation: 'Windkraft Österreich, „Wie funktioniert ein Windrad?“',
		url: 'https://www.windfakten.at/wind-energie/wie-funktioniert-ein-windrad'
	},
	{
		id: 6,
		citation: 'H. Ritchie, „How does the land use of different electricity sources compare?“, Our World in Data, Juni 2022. Zugegriffen: 21. April 2026.',
		url: 'https://ourworldindata.org/land-use-per-energy-source'
	},
	{
		id: 7,
		citation: 'D. EVN / Matejschek, „Repowering Windpark Japons startet“. Zugegriffen: 19. April 2026.',
		url: 'https://www.evn.at/home/presse/repowering-windpark-japons-startet'
	},
	{
		id: 8,
		citation:
			'S. Scherhaufer, F. Part, und P. Beigl, „Das Sekundärressourcenpotenzial aus Windkraft- und Photovoltaikanlagen“, Österr. Wasser- Abfallwirtsch., Bd. 73, Nr. 1–2, S. 36–48, Feb. 2021, doi: 10.1007/s00506-020-00723-3.'
	},
	{
		id: 9,
		citation: 'Windkraft Österreich, „Windkraft in Österreich: Zahlen und Statistiken“, Jänner 2026.',
		url: 'https://www.wind.at/aktuelles/windkraft-in-oesterreich'
	},
	{
		id: 10,
		citation: 'WWF, „Good News: 90 Seeadler-Paare leben bereits in Österreich“. Zugegriffen: 29. April 2026.',
		url: 'https://www.wwf.at/good-news-90-seeadler-paare-leben-bereits-in-oesterreich/'
	},
	{
		id: 11,
		citation: 'S. Schreiner, „Neue Höhen für den Kaiseradler“.',
		url: 'https://www.birdlife.at/artikel/neue-hoehen-fuer-den-kaiseradler/'
	},
	{
		id: 12,
		citation: 'Nationalpark Donau-Auen, „Großtrappe“. Zugegriffen: 29. April 2026.',
		url: 'https://www.donauauen.at/wissen/natur-wissenschaft/fauna/grosstrappe-otis-tarda'
	},
	{
		id: 13,
		citation: 'Nationalpark Donau-Auen, „Milane - Rotmilan“. Zugegriffen: 29. April 2026.',
		url: 'https://www.donauauen.at/wissen/natur-wissenschaft/fauna/rotmilan-milvus-milvus'
	},
	{
		id: 14,
		citation: 'ORF NÖ, „Gefährdeter Falke brütet auf Strommasten“. Zugegriffen: 29. April 2026.',
		url: 'https://noe.orf.at/stories/3327808/'
	},
	{
		id: 15,
		citation: 'F. Rechsteiner, „Recycling-Potential von Windenergieanlagen“, Fraunhofer-Institut, 2025.',
		url: 'https://www.igcv.fraunhofer.de/de/presse_downloads/pressemitteilungen/recycling-potential-von-windenergieanlagen-.html'
	},
	{
		id: 16,
		citation: 'Windfakten, „Recycling“. Zugegriffen: 19. April 2026.',
		url: 'https://www.windfakten.at/natur-umweltschutz/umweltschutz/recycling'
	},
	{
		id: 17,
		citation:
			'L. Mishnaevsky, A. Tempelis, Y. Belahurau, und N. F.-J. Johansen, „Microplastics Emission from Eroding Wind Turbine Blades: Preliminary Estimations of Volume“, Energies, Bd. 17, Nr. 24, S. 6260, Jan. 2024, doi: 10.3390/en17246260.'
	},
	{
		id: 18,
		citation:
			'J. Bertling, R. Bertling, und L. Hamann, „Kunststoffe in der Umwelt: Mikro- und Makroplastik. Ursachen, Mengen, Umweltschicksale, Wirkungen, Lösungsansätze, Empfehlungen. Kurzfassung der Konsortialstudie“, Fraunhofer-Institut für Umwelt-, Sicherheits- und Energietechnik UMSICHT, 2018, doi: 10.24406/uMsiCht-n-497117.'
	},
	// Aktuell von keinem Text zitiert: FAQ 4 belegte damit „weniger als 0,02 %
	// des Mikroplastik-Ausstoßes”; die Redaktion hat die Aussage am 11.11.2026
	// auf „weniger als 1 %” mit der Fraunhofer-UMSICHT-Studie [18] umgestellt.
	// Der Eintrag bleibt stehen, damit die Nummerierung aller übrigen Belege
	// gleich bleibt.
	{
		id: 19,
		citation: 'Bundesverband WindEnergie (BWE), „Positionspapier: Erosion an Rotorblättern von Windenergieanlagen”, 2024.'
	},
	{
		id: 20,
		citation: 'EVN, „Warum stehen Windräder still?“ Zugegriffen: 20. Juli 2026.',
		url: 'https://www.evn.at/home/evn-blog/energie/warum-stehen-windraeder-still'
	},
	{
		id: 21,
		citation: 'ÖVE/ÖNORM EN 61400-11:2013 „Windenergieanlagen, Teil 11, Schallmessverfahren“, 1. Oktober 2013.'
	},
	{
		id: 22,
		citation: 'F. Ludwig, „Eiswurf von Windrädern: Wie groß ist die Gefahr wirklich?“, Mitteldeutscher Rundfunk, 2026.',
		url: 'https://www.mdr.de/nachrichten/deutschland/panorama/windraeder-eiswurf-gefahr-sicherheit-abstand-100.html'
	},
	{
		id: 23,
		citation: 'EAG-Marktprämienverordnung-Novelle 2026, Jahrgang 2026, Teil 2, Wien. Zugegriffen: 20. April 2026.',
		url: 'https://www.ris.bka.gv.at/Dokumente/BgblAuth/BGBLA_2026_II_13/BGBLA_2026_II_13.pdf'
	},
	{
		id: 24,
		citation: 'E-Control, „Referenzmarktwert gemäß § 13 Erneuerbaren-Ausbau-Gesetz (EAG)“. Zugegriffen: 20. April 2026.',
		url: 'https://www.e-control.at/referenzmarktwert'
	},
	{
		id: 25,
		citation: 'M. Lagetar, „Munderfing: Glasfaser auch in entlegenen Orten“, nachrichten.at. Zugegriffen: 20. April 2026.',
		url: 'https://www.nachrichten.at/oberoesterreich/innviertel/munderfing-glasfaser-auch-in-entlegenen-orten;art70,3535424'
	},
	{
		id: 26,
		citation: 'P. Plattner, „Windkraft-Gemeinde zahlt jeder Familie bis zu 720 Euro im Jahr“, 5 Minuten. Zugegriffen: 20. April 2026.',
		url: 'https://www.5min.at/oesterreich/5202510071434/windkraft-gemeinde-zahlt-jeder-familie-bis-zu-720-euro-im-jahr/'
	},
	{
		id: 27,
		citation:
			'S. Lappöhn, C. Kimmich, E. Laa, und K. Plank, „Global denken, international abstimmen, lokal umsetzen – für eine erfolgreiche Energiewende“, 2022.',
		url: 'https://irihs.ihs.ac.at/id/eprint/6291/1/ihs-policy-brief-2022-lappoehn-kimmich-laa-plank-global-denken-erfolgreiche-energiewende.pdf'
	},
	{
		id: 28,
		citation:
			'S. Holzheu, „Infraschall im Auto (Turbodiesel)“, BayCEER, Universität Bayreuth, 2020. Zugegriffen: 10. August 2026.',
		url: 'https://www.bayceer.uni-bayreuth.de/infraschall/de/forschung/gru/html.php?id_obj=157452'
	},
	{
		id: 29,
		citation:
			'E. Katovich, „Quantifying the Effects of Energy Infrastructure on Bird Populations and Biodiversity“, Environ. Sci. Technol., Bd. 58, Nr. 1, S. 323–332, Jan. 2024, doi: 10.1021/acs.est.3c03899.',
		url: 'https://www.researchgate.net/publication/376925751_Quantifying_the_Effects_of_Energy_Infrastructure_on_Bird_Populations_and_Biodiversity'
	},
	{
		id: 30,
		citation: 'W.E.B. Windenergie, „Wind im Wald — Windpark Hardwald“. Zugegriffen: 11. November 2026.',
		url: 'https://www.web.energy/at-de/projekte/hardwald/wind-im-wald'
	},
	{
		id: 31,
		citation:
			'C. Kost, L. Müller, J. Schweiger, V. Fluri, und T. Schlegl, „Stromgestehungskosten erneuerbare Energien“, Fraunhofer-Institut für Solare Energiesysteme ISE, Juli 2024.',
		url: 'https://www.ise.fraunhofer.de/content/dam/ise/de/documents/publications/studies/DE2024_ISE_Studie_Stromgestehungskosten_Erneuerbare_Energien.pdf'
	},
	{
		id: 32,
		citation:
			'Oesterreichs Energie, „Kompass Energieunabhängigkeit: Jedes Jahr fossile Importe im Wert von 1.000 Windrädern“.',
		url: 'https://oesterreichsenergie.at/aktuelles/presseinformationen/detailseite/kompass-energieunabhaengigkeit-jedes-jahr-fossile-importe-im-wert-von-1000-windraedern'
	},
	{
		id: 33,
		citation: 'BirdLife Österreich, „Monitoring der Brutvögel Österreichs“.',
		url: 'https://www.birdlife.at/vogelschutz/forschung-und-monitoring/monitoring-der-brutvoegel-oesterreichs/'
	},
	{
		id: 34,
		citation: 'Österreichischer Alpenverein, „Gletschermonitor“.',
		url: 'https://www.alpenverein.at/gletschermonitor'
	}
];

export function getSource(id: number): Source | undefined {
	return sources.find((s) => s.id === id);
}
