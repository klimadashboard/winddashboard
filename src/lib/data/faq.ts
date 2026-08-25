export type GraphicKey =
	| "windrad-height"
	| "rotor-growth"
	| "bird-population"
	| "sound-level"
	| "infrasound"
	| "merit-order"
	| "land-use"
	| "repowering"
	| "winter-power";

export interface FaqItem {
	id: number;
	question: string;
	answer: string[];
	graphic?: GraphicKey;
	// Short "Quelle: …" line rendered under the graphic. May contain [n] footnote markers.
	graphicCaption?: string;
}

export interface FaqCategory {
	id: string;
	label: string;
	color: string;
	bg: string;
	items: FaqItem[];
}

export interface InfoCard {
	id: string;
	title: string;
	lead: string;
	content: string[];
	graphic?: GraphicKey;
	graphicCaption?: string;
}

export const infoCards: InfoCard[] = [
	{
		id: "winter-power",
		title: "Windkraft = Winterkraft",
		lead: "Die verschiedenen erneuerbaren Energiequellen ergänzen sich gegenseitig.",
		content: [
			"Die Windkraft produziert vor allem im Winter Strom, während Photovoltaik vor allem im Sommer liefert. Zwei Drittel des jährlichen Windstroms werden im Winterhalbjahr erzeugt – also genau dann, wenn der Wasserstand der Flüsse niedrig ist und die Sonne weniger scheint.",
			"Die verschiedenen erneuerbaren Energiequellen ergänzen sich gegenseitig, weshalb es einen optimalen Mix aus Wind, Wasser und Sonne sowie den Ausbau von Speichern und Stromnetzen braucht.",
		],
		graphic: "winter-power",
		graphicCaption:
			"Energy Charts [1], Durchschnitt der täglichen Stromerzeugung in Österreich 2020–2025",
	},
	{
		id: "technical-data",
		title: "Größe & Technik",
		lead: "Moderne Windräder sind leistungsfähiger und effizienter als je zuvor.",
		content: [
			"Windräder sind heute leistungsfähiger und effizienter als je zuvor. Noch 2009 lag die typische Nennleistung der neu gebauten Windräder unter 3 MW [2]. Die heute gebauten Anlagen haben inzwischen eine Leistung von 7 MW, eine Nabenhöhe von ca. 190 m und einen Rotordurchmesser von 170 m [3]. Damit erreichen moderne Windräder eine Gesamthöhe von bis zu 280 m.",
			"Mit der zunehmenden Größe der Windräder ist die erzeugte Strommenge deutlich angestiegen. Während ein Windrad mit einer Leistung von 3 MW pro Jahr etwa 6 Mio. kWh Strom erzeugt, liefern moderne Windräder mit 7 MW heute rund 18 Millionen kWh pro Jahr – also etwa dreimal so viel Strom.",
			"Moderne Windräder liefern also dreimal so viel Strom pro Anlage wie noch vor gut zehn Jahren.",
			"Windenergie ist außerdem sehr effizient: Ein Windrad erzeugt je nach Standort in 2,5 bis 11 Monaten die Energie, die es zur Herstellung braucht. [4]",
		],
		graphic: "rotor-growth",
		graphicCaption: "Quelle: IG Windkraft [5]",
	},
	{
		id: "land-use",
		title: "Flächenbedarf",
		lead: "99 % der Fläche eines Windparks bleiben weiterhin land- und forstwirtschaftlich nutzbar.",
		content: [
			"Hier siehst du eine schematische Darstellung eines Windparks. Die dunkelblau dargestellte Windparkfläche umfasst die gesamte Fläche, auf der der Windpark steht. Die für den Bau des Windparks notwendigen Zufahrtswege sowie die Kranstellfläche sind rot dargestellt und bleiben wasserdurchlässig (rund 2.300 m²). Nur das Fundament in dunkelrot wird versiegelt (ca. 500 m²). Unten siehst du die Flächen im richtigen Größenverhältnis. Nur rund 1 % der gesamten Windparkfläche wird für Zufahrtswege, Kranstellfläche und Fundament des Windrads benötigt, der Rest an Grünfläche bzw. Wald bleibt bestehen.",
			"Windkraft braucht verhältnismäßig wenig Platz. Im Vergleich zu anderen Energieformen (Kohle, Gas) ist Windenergie sehr flächeneffizient. [6]",
			"99 % der Fläche eines Windparks bleiben weiterhin land- und forstwirtschaftlich nutzbar.",
			"Nur rund 0,5 % der Fläche werden für Kranstellfläche und Zufahrtswege benötigt – diese bleiben geschottert und damit wasserdurchlässig. Weitere 0,5 % entfallen auf das Fundament, das versiegelt wird.",
		],
		graphic: "land-use",
	},
	{
		id: "repowering",
		title: "Repowering",
		lead: "Neue Windräder erzeugen ein Vielfaches mehr Strom – bei weniger Anlagen.",
		content: [
			"Beim Repowering des Windparks Japons (Bezirk Horn) 2021 wurden 7 alte Windräder durch 3 neue ersetzt. Während die 7 alten Strom für 6.000 Haushalte lieferten, decken die 3 neuen den Energiebedarf von 10.000 Haushalten – eines der neuen Windräder erzeugt also knapp viermal so viel wie ein altes. [7]",
			"Alte Windräder können bereits zu 80–90 % wiederverwertet werden. Der Turm aus Stahl wird eingeschmolzen, das Fundament im Straßenbau genutzt und die Rotorblätter als Ersatzbrennstoff in Zementwerken eingesetzt. [8]",
		],
		graphic: "repowering",
	},
];

export const faqCategories: FaqCategory[] = [
	{
		id: "nature",
		label: "Natur & Umwelt",
		color: "#c0392b",
		bg: "#fdf4f3",
		items: [
			{
				id: 1,
				question: "Wieso baut man Windräder im Wald?",
				answer: [
					"Wie in der Karte oben ersichtlich, scheiden viele Flächen für Windkraft in Österreich aufgrund der strengen Mindestabstände zu Siedlungsgebieten von vornherein aus. Unter den verbleibenden geeigneten Standorten befinden sich daher häufig auch Waldflächen – meist bewirtschaftete Wälder, nicht unberührte Naturflächen.",
					"Die tatsächlich dauerhaft beanspruchte Waldfläche bei einem Wald-Windpark ist gering: Gerodete Flächen müssen durch Ausgleichsflächen wieder aufgeforstet werden. Rund 99 % der Fläche eines Windparks bleiben weiterhin forstwirtschaftlich nutzbar.",
					"Windkraft im Wald ist zudem kein neues oder ungewöhnliches Konzept: In Deutschland stehen heute etwa doppelt so viele Windräder im Wald, wie in ganz Österreich insgesamt errichtet sind. Auch in Österreich gibt es Erfahrung damit: Der erste Wald-Windpark wurde bereits 2003 in Betrieb genommen (Sternwald, Oberösterreich).",
					"Der biologische Hauptaktivitätsraum im Wald geht vom Boden bis knapp über die Baumspitzen (also bis ca. 50 m über dem Boden). Die Windrad-Flügelunterkante befindet sich auf ca. 90 m über dem Boden – es liegen also 40 m zwischen biologischem Hauptaktivitätsraum und Windradflügel. Das spricht übrigens auch für die neueren, größeren Anlagen, da sich die Rotorblätter nun weit über den Baumkronen drehen. Im Vergleich zum Ackerland ist im Wald auf der Höhe der Windradflügel weniger biologische Aktivität vorzufinden.",
				],
				graphic: "windrad-height",
			},
			{
				id: 2,
				question: "Gefährden Windräder die Biodiversität, insbesondere Vögel?",
				answer: [
					"Bei Windkraftprojekten erfolgt nach umfassenden Umweltuntersuchungen (1- bis 2-jährige Vogel- & Fledermausuntersuchung) eine sorgfältige naturschutzfachliche Planung. Der Standort wird so gewählt, dass Auswirkungen auf sensible Lebensräume möglichst gering sind.",
					"Bei manchen Standorten werden sogenannte Antikollisionssysteme eingesetzt, durch die potentielle Kollisionen von Vögeln und Windrädern sehr wirksam vermieden werden können. Dabei wird eine Kamera am Windrad montiert, die mit KI-Unterstützung gefährdete Arten wie z. B. den Rotmilan in Echtzeit erkennt und die Anlage bei Kollisionsgefahr ausschaltet.",
					"Während Windräder einzelne Vögel töten können, zeigen Studien, dass sie keinen messbaren Einfluss auf Vogelpopulationen haben. Andere Energieerzeugungstechnologien, wie zum Beispiel Öl- oder Gasbohrungen, haben im Gegensatz dazu einen signifikanten negativen Effekt auf Vogelpopulationen: Neue Anlagen zur Förderung von Öl und Gas vermindern umliegende Vogelpopulationen im Mittel um rund 15 Prozent.",
					"Aktuell verzeichnen insbesondere Feld- und Wiesenvogelarten einen starken Rückgang, vor allem aufgrund von intensiver Nutzung der Landschaft. Windkraftsensible Arten (bspw. Großgreifvögel) verzeichnen dagegen seit einigen Jahrzehnten kontinuierliches Wachstum.",
				],
				graphic: "bird-population",
				graphicCaption:
					"Windkraft: IG Windkraft [9] · Brütende Seeadler: WWF [10] · Brütende Kaiseradler: BirdLife [11] · Großtrappen: Nationalpark Donau-Auen [12] · Brütende Rotmilane: Nationalpark Donau-Auen [13] · Brütende Sakerfalken: ORF NÖ [14]",
			},
			{
				id: 3,
				question: "Können Windräder recycelt werden?",
				answer: [
					"Wenn ein Windrad seine rund 20-jährige Lebensdauer erreicht hat, wird es abgebaut und kann zu 80–90 % wiederverwertet werden. [8] Der Turm aus Stahl kann wiederverwertet werden, während das Fundament aus Zement beispielsweise im Straßenbau genutzt werden kann.",
					"Die Rotorblattentsorgung ist jedoch deutlich schwieriger, da eine Vielzahl an verschiedenen Materialien verbaut ist. Aktuell werden die Rotorblätter als Ersatzbrennstoff in Zementwerken eingesetzt. Es gibt mittlerweile aber auch vermehrt Unternehmen, die sich dem Rotorblatt-Recycling widmen. Bisher gab es für die recycelten Materialien noch nicht ausreichend Nachfrage – diese könnte beispielsweise durch eine Recyclingquote gesteigert werden. [15]",
					"Derzeit werden jedoch fast alle abgebauten Windräder am Second-Hand-Markt verkauft. Ganz neue Windradflügel können auch schon in ihre Einzelkomponenten zerlegt und wieder als Ausgangsstoffe zur Verfügung gestellt werden. [16]",
				],
			},
			{
				id: 4,
				question: "Verursachen Windräder gefährliche Mengen an Mikroplastik?",
				answer: [
					"Durch Witterungseinflüsse wie Regen und Hagel kommt es an den Beschichtungen der Rotorblätter zu geringfügigem Abrieb. Eine Studie der Technischen Universität Dänemark hat die Menge an Mikroplastik von Windrädern untersucht und kommt bei Onshore-Windrädern auf das Ergebnis von 8–50 g pro Jahr pro Blatt. [17]",
					"Deutlich mehr Abrieb wird im Straßenverkehr durch den Reifenabrieb erzeugt oder auch durch den Abrieb von Schuhsohlen oder Textilien. [18] In Deutschland macht die Windkraft weniger als 0,02 % des gesamten Mikroplastik-Ausstoßes aus. [19]",
				],
			},
			{
				id: 5,
				question: "Wieso baut man Windräder im alpinen Raum?",
				answer: [
					"Windkraft im alpinen Raum ist kein Neuland. In der Schweiz wurde bereits 2002 der erste Windpark Gütsch ob Andermatt auf 2.300 m errichtet. Aufgrund der Windverhältnisse und der hohen Winterproduktion wurde der Standort weiter ausgebaut. Mittlerweile stehen dort 5 Windräder, die rund 5.000 Haushalte mit Strom versorgen.",
					"Auch in Österreich zeigen bestehende Windparks in der Steiermark und in Kärnten, wie sich Strom aus Windkraft auch in höheren Lagen erzeugen lässt. Der Windpark Pretul auf rund 1.500 bis 1.600 m Seehöhe zählt zu den windstärksten Regionen Österreichs. Dort stehen 14 Windräder, die rund 38.000 Haushalte mit erneuerbarem Strom versorgen.",
					"Windräder greifen sichtbar in die Landschaft ein, besonders in den Bergen. Allerdings hat auch der Skitourismus in den letzten Jahrzehnten das Landschaftsbild verändert. Hinzu kommt, dass der Klimawandel gerade in alpinen Regionen starke Veränderungen mit sich bringt: Die Gletscher befinden sich im Rückzug – in Österreich wird es 2050 keine Gletscher mehr geben, wie der Alpenverein warnt.",
					"Wenn Windräder in verschiedenen Regionen in Österreich stehen, sorgt dies für eine zuverlässigere Stromversorgung. Denn irgendwo in Österreich weht immer der Wind. So lässt sich erneuerbare Energie besser über das ganze Jahr nutzen.",
				],
			},
		],
	},
	{
		id: "health",
		label: "Gesundheit & Anrainer:innen",
		color: "#b45309",
		bg: "#fffbeb",
		items: [
			{
				id: 6,
				question: "Welche Schall- und Schattenregelungen gelten?",
				answer: [
					"Österreich hat strenge Auflagen für Schallemission und Schattenwurf durch Windräder. Der Schatten eines Windrads auf ein Wohngebäude ist auf maximal 30 Minuten pro Tag und 30 Stunden pro Jahr begrenzt.",
					"Der Schall eines Windrads darf nicht mehr als 3 Dezibel (dB) über dem Hintergrundgeräuschpegel der ruhigsten Tages- bzw. Nachtzeit liegen [21]. In leiseren Regionen müssen Windräder damit auch leiser sein. Sollten die Lärmvorschriften in einer Gemeinde trotz Mindestabstand nicht eingehalten werden können, müssen Windräder noch weiter von den Wohnhäusern wegrücken.",
					"In 1.200 m Entfernung erreicht ein Windrad rund 35–40 dB – vergleichbar mit dem Brummen eines Kühlschranks, allerdings nur bei voller Leistung. Da Wind bereits an sich hörbar ist, überdeckt der Wind die Geräusche des Windrads (Wind ca. 35 dB). In windschwachen, leisen Nächten läuft die Anlage entsprechend leiser oder steht still, sodass sie kaum oder gar nicht wahrnehmbar ist.",
				],
				graphic: "sound-level",
			},
			{
				id: 7,
				question:
					"Was ist Infraschall, und kann er von Windrädern meine Gesundheit gefährden?",
				answer: [
					"Während es sich bei hörbarem Schall um sehr schnelle Schwingungen der Luft handelt, bezeichnet Infraschall sehr langsame, niederfrequente Luftschwingungen, die wir mit dem menschlichen Ohr nicht wahrnehmen können. Fast jedes Schallphänomen hat auch Infraschallanteile – typische Quellen sind zum Beispiel Autos, Waschmaschinen, Kühlschränke oder auch das Trampolinspringen und Türenschließen.",
					"Auch bei einem Windrad entstehen Luftschwingungen und somit Infraschall – dabei handelt es sich aber um gesundheitlich unbedenkliche Pegel. Eine Untersuchung zeigt: Eine 3,5-stündige Autofahrt verursacht die gleiche Infraschall-Belastung wie 27 Jahre in 300 m Abstand zu einem Windrad. [28]",
					"Auch ein Kindertrampolin im Garten erzeugt ein Vielfaches mehr Infraschall als ein Windrad.",
				],
				graphic: "infrasound",
			},
			{
				id: 8,
				question: "Ist der Eisabfall von Windrädern gefährlich?",
				answer: [
					"Bei Minusgraden kann sich auch bei Windrädern, genauso wie bei Bäumen oder Häusern, Eis bilden. In diesem Fall werden Windräder umgehend abgeschaltet (dafür gibt es eigene Sensoren). Erst wenn sich das Eis wieder vom Windrad gelöst hat, dürfen die Anlagen wieder in Betrieb genommen werden.",
					"Bei modernen Windrädern kommt teilweise eine sogenannte Rotorblattheizung zum Einsatz, mit deren Hilfe die Windradflügel abgetaut werden.",
					"So wie bei Eiszapfen auf Hausdächern und Bäumen sollte man in dieser Zeit nicht unter dem Windrad stehen. Daher werden Warnschilder aufgestellt, die bei Vereisung davor warnen, den Platz unter dem Windrad zu betreten (bei modernen Anlagen sind das ca. 300 m rund um das Windrad). [22] Zu diesen Zeiten ist es jedoch allgemein gefährlich, sich im Wald aufzuhalten, weil sich mit hoher Wahrscheinlichkeit auch auf Bäumen Eiszapfen gebildet haben.",
				],
			},
		],
	},
	{
		id: "finance",
		label: "Geld, Finanzen, Kosten",
		color: "#059669",
		bg: "#f0fdf4",
		items: [
			{
				id: 9,
				question: "Wird der Strom durch Windräder billiger?",
				answer: [
					"Windstrom zählt zu den günstigsten Formen der Stromerzeugung. Derzeit ist der Strompreis oft hoch, weil besonders im Winter teure Gaskraftwerke zugeschaltet werden müssen, um die Nachfrage zu decken. Je mehr erneuerbare Energien im Netz sind, desto seltener müssen fossile Kraftwerke einspringen und desto günstiger wird der Strom. Darüber hinaus bieten viele Windparkbetreiber den Anrainer:innen direkt günstigeren Strom an, beispielsweise über Energiegemeinschaften oder eigene Stromtarife. Dabei können sich Haushalte zusammenschließen und Windstrom zu reduzierten Netzkosten beziehen.",
					"In der Grafik siehst du, wie sich der Strompreis in Europa bildet (durch die sogenannte „Merit-Order“). Auf der senkrechten Achse sieht man die Kosten, also wie teuer die Stromerzeugung ist. Auf der waagerechten Achse ist dargestellt, wie viel Strom zu einem bestimmten Zeitpunkt insgesamt benötigt bzw. erzeugt wird. Generell wird der Strom immer zuerst vom günstigsten Kraftwerk gedeckt, also Energie aus Wasser-, Wind- und Sonnenkraft, denn diese haben die niedrigsten variablen Kosten. Wenn die Nachfrage jedoch höher ist als das, was mit Erneuerbaren zu einem bestimmten Zeitpunkt produziert werden kann, folgen Technologien wie Atomkraftwerke, Kohlekraftwerke und Gaskraftwerke, die deutlich teurer sind. Um den Strombedarf zu decken, werden die Kraftwerke nacheinander eingesetzt: Zuerst produzieren die günstigen Anlagen Strom, reicht das nicht aus, werden nach und nach auch die teureren Kraftwerke zugeschaltet, bis genug Strom vorhanden ist. Entscheidend für die Kosten ist dabei das letzte Kraftwerk, das noch benötigt wird, um die Nachfrage vollständig zu decken – denn dessen variable Kosten bestimmen den Strompreis. Heutzutage ist dies nach wie vor oft ein Gaskraftwerk, vor allem in den Wintermonaten – das treibt den Preis in die Höhe. Je mehr Erneuerbare ans Netz gehen, desto weniger häufig braucht man die teuren, fossilen Kraftwerke. Langfristig können diese so aus dem Markt gedrängt und durch billigen, erneuerbaren Strom wie Wind oder PV ersetzt werden.",
				],
				graphic: "merit-order",
			},
			{
				id: 10,
				question: "Wie viel Geld bekommen die Betreiber?",
				answer: [
					"Windkraftbetreiber verkaufen ihren Strom am freien Markt. Der Staat garantiert ihnen dabei über 20 Jahre einen Mindestpreis – derzeit 9,92 ct/kWh. Liegt der Marktpreis darunter, gleicht der Staat die Differenz aus. Liegt der Marktpreis darüber, bekommen sie kein zusätzliches Geld.",
					"Beispiel: Im März 2026 liegt der Referenzmarktwert für Windkraftanlagen bei 11,33 ct/kWh [24] – über den zugesicherten 9,92 ct/kWh. Die Unternehmen bekommen also kein zusätzliches Geld vom Staat. Sinkt der Marktstrompreis hingegen z. B. auf 6 ct/kWh, wird den Windkraftunternehmen die Differenz von 3,92 ct/kWh vom Staat ausbezahlt. [23]",
					"Liegt der Strompreis deutlich über dem anzulegenden Wert, muss der Betreiber einen Teil des Mehrerlöses zurückzahlen – das Geld wird auf ein Konto bei der Erneuerbaren-Abwicklungsstelle eingezahlt. Der garantierte Minimalerlös pro verkaufter kWh dient vor allem der Sicherung der Finanzierung von Windkraftprojekten.",
				],
			},
			{
				id: 11,
				question: "Wie viel Geld bekommen die Gemeinden?",
				answer: [
					"Eine Gemeinde bekommt für ein Windrad etwa 25.000 bis 50.000 € pro Jahr (abhängig von der Leistung des Windrads: zwischen 5.000–7.000 € pro MW).",
					"Dieses Geld kann die Gemeinde für verschiedene Zwecke verwenden: In Munderfing (OÖ) wurde beispielsweise mit dem Geld des Windparks das Glasfasernetz in der Gemeinde ausgebaut [25]. Die Gemeinde Höflein (NÖ) zahlt jeder Familie eine jährliche finanzielle Energieunterstützung aus, generiert durch die Einnahmen des Windparks vor Ort [26].",
					"Bei neuen Windparkprojekten wird den Gemeindebürger:innen häufig auch ein fixer, verbilligter Stromtarif angeboten. Dies ist erst mit dem neuen Förderregime des Erneuerbaren-Ausbau-Gesetzes seit Ende 2022 möglich.",
				],
			},
			{
				id: 12,
				question: "Was sind die Auswirkungen auf die heimische Wirtschaft?",
				answer: [
					"Windkraft macht uns unabhängig von fossilen Energieimporten aus dem Ausland. Derzeit fließen jährlich rund 10 Mrd. Euro für Öl- und Gasimporte ab – Geld, das stattdessen in regionale Wertschöpfung und Arbeitsplätze investiert werden könnte.",
					"Windkraftprojekte schaffen Arbeitsplätze vor Ort: in Planung, Bau, Wartung und Betrieb – vor allem im laufenden Betrieb, weniger bei der Installation.",
					"Bei erneuerbaren Energien verbleiben von jedem ausgegebenen Euro im Mittel 96 Cent in Österreich, während es bei fossilen Energien nur 55 Cent sind. Bei Erneuerbaren bleibt also fast doppelt so viel Wertschöpfung in Österreich als bei fossilen Energien. [27]",
				],
			},
		],
	},
	{
		id: "energiesystem",
		label: "Energiesystem & Betrieb",
		color: "#2563eb",
		bg: "#eff6ff",
		items: [
			{
				id: 13,
				question: "Warum stehen Windräder still?",
				answer: [
					"Wenn sich ein Windrad nicht dreht, obwohl Wind weht, kann das verschiedene Gründe haben. Damit ein Windrad Strom erzeugen kann, muss zunächst eine bestimmte Mindestwindgeschwindigkeit erreicht werden. Bei sehr starkem Wind werden die Anlagen aus Sicherheitsgründen automatisch abgeschaltet, um Schäden zu vermeiden.",
					"Auch regelmäßige Wartungs- und Reparaturarbeiten können dazu führen, dass ein Windrad vorübergehend stillsteht. Je nach Größe des Defektes und Verfügbarkeit von Ersatzteilen kann der Stillstand mitunter auch mehrere Wochen dauern.",
					"In manchen Fällen werden Windräder außerdem zeitweise abgeschaltet, um geschützte Vogel- oder Fledermausarten zu schützen, oder wenn sich im Winter Eis auf den Rotorblättern gebildet hat (dafür gibt es eigene Sensoren). Erst nach dem Abtauen des Eises und einer Kontrolle kann das Windrad wieder eingeschaltet werden. [20]",
				],
			},
			{
				id: 14,
				question: "Braucht es in jedem Bundesland ein Windrad?",
				answer: [
					"Um die Energiewende zu schaffen, müssen die Windkraft-Potenziale in allen Bundesländern genutzt werden. Denn eine geografische Verteilung gleicht Wetterschwankungen aus: Wenn in Ostösterreich kein Wind weht, weht er möglicherweise im Westen. Eine breite Streuung der Standorte sorgt damit für eine stabilere Stromerzeugung über das gesamte Jahr.",
					"Gleichzeitig reduziert die Verteilung die Belastung der Stromnetze. Würde der gesamte Windstrom in Niederösterreich und Burgenland erzeugt und dann über weite Strecken in den Westen transportiert werden, müsste das Netz noch stärker ausgebaut werden.",
					"Mit Windrädern leistet außerdem jedes Bundesland einen Beitrag zur eigenen Versorgungssicherheit. Österreich importiert derzeit vor allem in den Wintermonaten Strom, weil Sonne und Wasserkraft dann weniger liefern. Windkraft erzeugt genau in dieser Zeit am meisten Strom und trägt damit zum Schließen der Winterstromlücke bei.",
					'Statt „entweder-oder" braucht es deshalb „sowohl-als-auch"-Lösungen: Jedes Bundesland leistet entsprechend seines Potenzials einen Beitrag.',
				],
			},
		],
	},
];
