import { STATE } from './regionIntro';

export type Step = {
	number: number;
	title: string;
	// The body/authority responsible for this step (e.g. "Land", "Gemeinde",
	// "Windkraftbetreiber"). Rendered as its own badge instead of appended to
	// the title in parentheses.
	responsible?: string;
	paragraphs: string[];
};

export type StateContent = {
	intro?: string;
	steps: Step[];
};

// Shown once, above every state's step breakdown.
export const GENERAL_INTRO =
	'In Österreich gelten strenge gesetzliche Vorgaben dafür, wo und unter welchen Bedingungen ein Windrad errichtet werden darf. Der Weg von der ersten Idee bis zur tatsächlichen Errichtung eines Windrads ist daher mehrstufig und umfasst wirtschaftliche, technische, rechtliche und ökologische Prüfungen. Die Gesamtdauer von Windkraftprojekten in Österreich (von der Planung bis zur Errichtung) liegt im Durchschnitt bei 5 bis 8 Jahren.';

const STANDORTPRUEFUNG_KURZ: string[] = [
	'Am Beginn jedes Windkraftprojekts steht die sorgfältige Prüfung eines möglichen Standorts. Dabei wird unter anderem untersucht, ob ausreichend Wind vorhanden ist und ob ein Anschluss an das Stromnetz technisch möglich ist. Ebenso werden die Zufahrtsmöglichkeiten für Bau und Wartung sowie raumordnungsrechtliche Rahmenbedingungen geprüft (z.B. Hangneigung).',
	'Zeigt diese erste Prüfung, dass ein Standort grundsätzlich geeignet ist, werden die benötigten Grundstücksflächen gesichert. In der Praxis geschieht dies meist über Pachtverträge mit den Grundstückseigentümer:innen.',
	'Dann beginnt die wirtschaftlich-technische Detailprüfung. Dazu werden in der Regel 1 Jahr lang Windmessungen durchgeführt. Aus den Messdaten wird berechnet, wie viel Strom ein Windrad an diesem Standort voraussichtlich erzeugen könnte. Auf dieser Grundlage können Betreiber einschätzen, ob sich das Projekt wirtschaftlich lohnt und welcher Windrad-Typ geeignet ist. Die Windmessung dient ausschließlich der wirtschaftlich-technischen Projektvalidierung und stellt noch keine Genehmigung für den Bau dar.',
	'Auch der Netzanschluss muss geprüft und möglichst frühzeitig gesichert werden, da die verfügbaren Netzkapazitäten begrenzt sind.',
];

const STANDORTPRUEFUNG_KONKRET: string[] = [
	'Am Beginn jedes konkreten Windkraftprojekts steht die sorgfältige Prüfung eines möglichen Standorts. Dabei wird unter anderem untersucht, ob ausreichend Wind vorhanden ist und ob ein Anschluss an das Stromnetz technisch möglich ist. Ebenso werden die Zufahrtsmöglichkeiten für Bau und Wartung sowie raumordnungsrechtliche Rahmenbedingungen geprüft (z.B. Hangneigung).',
	...STANDORTPRUEFUNG_KURZ.slice(1),
];

const UVP_STANDARD: string[] = [
	'Ob ein Windrad schlussendlich tatsächlich gebaut werden darf, entscheidet sich im Genehmigungsverfahren. Bei großen Projekten passiert dies in Form einer Umweltverträglichkeitsprüfung (UVP), im Zuge derer zahlreiche Themen geprüft werden: ökologische Eignung, Schattenwurf, Schallimmissionen, Auswirkungen auf die Boden- und Landwirtschaft und Grundwasserhydrologie.',
	'Ein besonderer Schwerpunkt liegt auf dem Natur- und Artenschutz. Dazu werden meist über zwei Jahre hinweg Untersuchungen zur Aktivität von Vögeln und Fledermäusen durchgeführt. Die Ergebnisse dienen unter anderem dazu, Abschaltzeiten festzulegen. Diese sorgen dafür, dass Windräder während besonders sensibler Aktivitätszeiten automatisch stillstehen und so der Schutz der Tierwelt gewährleistet wird. Außerdem werden im Zuge der Umweltverträglichkeitsprüfung auch Ausgleichsmaßnahmen festgelegt, wie beispielsweise Aufforstungen oder Aufwertung anderer Lebensräume (Blühflächen oder Habitate für bestimmte Arten).',
	'Erst wenn diese Prüfungen positiv abgeschlossen sind und alle erforderlichen Genehmigungen vorliegen, darf gebaut werden.',
];

// Keys are state region IDs from base.klimadashboard.org/items/regions (layer=state)
export const stateContent: Record<string, StateContent> = {
	// Niederösterreich
	[STATE.NIEDERÖSTERREICH]: {
		intro: 'In Niederösterreich müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Zonierung',
				responsible: 'Land Niederösterreich',
				paragraphs: [
					'Neue Windräder können nur auf eigens dafür ausgewiesenen Flächen des Bundeslandes Niederösterreich errichtet werden (sogenannte Zonierung). Alle anderen Flächen sind Ausschlusszonen (98,5 % der Landesfläche). Bei der Ausweisung dieser Zonen gelten strenge Vorgaben: Es gilt ein Mindestabstand von 1.200 Metern zum nächsten Wohnbauland. In Nationalparks, Naturschutzgebieten, Landschaftsschutzgebieten und Biosphärenparks, Natura-2000-Vogelschutzgebieten, im Bereich von Naturschutzdenkmälern und eines UNESCO-Weltkulturerbes darf kein Windrad gebaut werden.',
					'Bereits bei der Zonierung wird die ökologische Eignung potenzieller Flächen geprüft. Fachorganisationen wie BirdLife sowie auch die Gemeinden werden dabei in die Bewertung miteinbezogen. In manchen Gebieten gibt es trotz geeigneter Flächen aktuell keine von der Landesregierung ausgewiesenen Windkraftzonen.',
				],
			},
			{
				number: 2,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KURZ,
			},
			{
				number: 3,
				title: 'Widmung',
				responsible: 'Gemeinde',
				paragraphs: [
					'Als nächstes müssen die für Windkraftprojekte geeigneten Flächen noch entsprechend umgewidmet werden. Für Windräder gibt es die Sonderwidmung „Grünland mit Windkraftnutzung". Die Widmung wird dabei vom betreffenden Gemeinderat beschlossen. Für die Widmung ist eine Strategische Umweltprüfung des Landes Niederösterreich notwendig. Diese dient dazu, voraussichtliche Umweltauswirkungen von Plänen und Programmen systematisch zu bewerten, bevor diese beschlossen oder umgesetzt werden.',
					'Hinweis zur Rechtslage: Befindet sich ein Windkraft-Projekt innerhalb der ausgewiesenen Zonen, fehlt aber die Widmung, kann der Betreiber trotzdem in das Genehmigungsverfahren gehen (siehe § 4a Abs 2 UVP-G).',
				],
			},
			{
				number: 4,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: UVP_STANDARD,
			},
		],
	},

	// Tirol
	[STATE.TIROL]: {
		intro: 'In Tirol müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: [
					'Am Beginn jedes Windkraftprojekts steht die sorgfältige Prüfung eines möglichen Standorts. Dabei wird untersucht, ob ausreichend Wind vorhanden ist, ob der Abstand zum nächsten Siedlungsgebiet ausreichend ist (abhängig vom Schall, meist ca. 800 - 1.200 m) und ob ein Anschluss an das Stromnetz technisch möglich ist. Ebenso werden die Zufahrtsmöglichkeiten für Bau und Wartung sowie raumordnungsrechtliche Rahmenbedingungen geprüft (z.B. Hangneigung).',
					'Zeigt diese erste Prüfung, dass ein Standort grundsätzlich geeignet ist, werden die benötigten Grundstücksflächen gesichert. In der Praxis geschieht dies meist über Pachtverträge mit den Grundstückseigentümer:innen.',
					'Dann beginnt die wirtschaftlich-technische Detailprüfung. Dazu werden in der Regel 1 Jahr lang Windmessungen durchgeführt. Aus den Messdaten wird berechnet, wie viel Strom ein Windrad an diesem Standort voraussichtlich erzeugen könnte. Auf dieser Grundlage können Betreiber einschätzen, ob sich das Projekt wirtschaftlich lohnt und welcher Windrad-Typ geeignet ist. Die Windmessung dient ausschließlich der wirtschaftlich-technischen Projektvalidierung und stellt noch keine Genehmigung für den Bau dar.',
					'Auch der Netzanschluss muss geprüft und möglichst frühzeitig gesichert werden, da die verfügbaren Netzkapazitäten begrenzt sind.',
				],
			},
			{
				number: 2,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: [
					...UVP_STANDARD.slice(0, 2),
					'Eine UVP ist bei Windkraftanlagen mit einer elektrischen Gesamtleistung von mindestens 30 MW erforderlich. Bei Anlagen über 1.000 Meter Seehöhe liegt die Schwelle bei 15 MW.',
					'Erst wenn alle Prüfungen positiv abgeschlossen sind und alle Genehmigungen vorliegen, darf mit dem Bau der Windräder begonnen werden.',
				],
			},
		],
	},

	// Steiermark
	[STATE.STEIERMARK]: {
		intro: 'In der Steiermark müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Zonierung',
				responsible: 'Land',
				paragraphs: [
					'Das Land Steiermark unterscheidet in der überörtlichen Raumplanung vier Arten von Flächen und schafft damit eine Unterscheidung von Flächen, wo Windkraft bevorzugt, gut möglich, grundsätzlich möglich oder ausgeschlossen ist. Im Zuge dieser Zonierung wird bereits die technische und ökologische Eignung potenzieller Flächen geprüft.',
					'Vorrangzonen = besonders geeignete Flächen, die vorrangig für Windkraft vorgesehen sind.',
					'Eignungszonen = grundsätzlich für Windkraft vorgesehen.',
					'Neutrale Zonen = diese Flächen werden für Windkraft weder aktiv eingeplant, noch kategorisch ausgeschlossen.',
					'Ausschlusszonen = für Windkraft ausgeschlossene Flächen.',
					'Generell ist in der Steiermark ein Mindestabstand von 1.000 Metern zum nächsten Wohnbauland einzuhalten.',
				],
			},
			{
				number: 2,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KURZ,
			},
			{
				number: 3,
				title: 'Widmung bzw. Ersichtlichmachung',
				responsible: 'Gemeinde',
				paragraphs: [
					'Je nachdem, in welcher Zone das Windkraft-Projekt geplant ist, muss die Gemeinde die Fläche für die Windkraft umwidmen oder lediglich ersichtlich machen.',
					'Vorrangzonen: Die Gemeinde muss die Zonierung lediglich im Flächenwidmungsplan ersichtlich machen. Es braucht keine zusätzliche Widmung der Gemeinde.',
					'Eignungszonen und neutrale Zonen: Die Gemeinde muss für Windkraftanlagen die Flächen widmen. Für die Widmung ist eine Strategische Umweltprüfung des Landes notwendig. Diese dient dazu, voraussichtliche Umweltauswirkungen von Plänen und Programmen systematisch zu bewerten, bevor diese beschlossen oder umgesetzt werden.',
				],
			},
			{
				number: 4,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: UVP_STANDARD,
			},
		],
	},

	// Kärnten
	[STATE.KÄRNTEN]: {
		intro: 'In Kärnten müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Zonierung',
				responsible: 'Land',
				paragraphs: [
					'Das Land Kärnten unterscheidet in der überörtlichen Raumplanung „Beschleunigungsgebiete", die für den Windkraftausbau genutzt werden dürfen, und Ausschlusszonen. Insgesamt hat das Land Kärnten vier Beschleunigungsgebiete ausgewiesen, die eine Fläche von ca. 730 ha umfassen. Das ist weniger als 0,1 % der Landesfläche, während über 99,9 % der Landesfläche Wind-Ausschlusszonen sind. Die Beschleunigungsgebiete wurden im Zuge der Ausweisung bereits einer strategischen Umweltprüfung unterzogen.',
					'Hinweis zur Rechtslage: Da die in Kärnten ausgewiesenen Beschleunigungsgebiete zu klein sind, um die gesetzlichen Windkraft-Ausbauziele zu erreichen, können Windräder auch außerhalb der Beschleunigungsgebiete gebaut werden (siehe § 4a Abs 3 UVP-G). Für den Bau eines Windrads außerhalb der Beschleunigungsgebiete braucht man jedoch die Zustimmung der Gemeinde.',
				],
			},
			{
				number: 2,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KURZ,
			},
			{
				number: 3,
				title: 'Kenntlichmachung im Flächenwidmungsplan',
				responsible: 'Gemeinde',
				paragraphs: [
					'Die Gemeinde muss die Zonierung lediglich im Flächenwidmungsplan ersichtlich machen. Es braucht keine zusätzliche Widmung der Gemeinde.',
					'Hinweis zur Rechtslage: Da die in Kärnten ausgewiesenen Beschleunigungsgebiete zu klein sind, um die gesetzlichen Windkraft-Ausbauziele zu erreichen, können Windräder auch außerhalb der Beschleunigungsgebiete gebaut werden (siehe § 4a Abs 3 UVP-G). Für den Bau eines Windrads außerhalb der Beschleunigungsgebiete braucht man jedoch die Zustimmung der Gemeinde.',
				],
			},
			{
				number: 4,
				title: 'Genehmigungsverfahren',
				responsible: 'Land',
				paragraphs: [
					'Ob ein Windrad schlussendlich tatsächlich gebaut werden darf, entscheidet sich im Genehmigungsverfahren. In Beschleunigungsgebieten wird eine sogenannte Grobprüfung durchgeführt. Diese dient dazu, zu prüfen, ob das Windrad tatsächlich im Beschleunigungsgebiet liegt, ob die festgelegten Minderungsmaßnahmen eingehalten werden und ob „voraussichtlich keine erheblichen (im Zeitpunkt der Ausweisung des Beschleunigungsgebiets) unvorhergesehenen nachteiligen Umweltauswirkungen" eintreten werden. Diese Grobprüfung muss binnen 45 Werktagen ab Vorlage der vollständigen Unterlagen durchgeführt werden.',
					'Außerhalb von Beschleunigungsgebieten hat das Land Kärnten den Bau von Windrädern eigentlich verboten. Da die in Kärnten ausgewiesenen Beschleunigungsgebiete zu klein sind, um die gesetzlichen Windkraft-Ausbauziele zu erreichen, können Windräder auch außerhalb der Beschleunigungsgebiete gebaut werden (siehe § 4a Abs 3 UVP-G). Für den Bau eines Windrads außerhalb der Beschleunigungsgebiete braucht man jedoch die Zustimmung der Gemeinde und muss auch hier ein Genehmigungsverfahren durchlaufen. Bei großen Projekten passiert dies in Form einer Umweltverträglichkeitsprüfung (UVP), im Zuge derer zahlreiche Themen geprüft werden: ökologische Eignung, Schattenwurf, Schallimmissionen, Auswirkungen auf die Boden- und Landwirtschaft und Grundwasserhydrologie. Ein besonderer Schwerpunkt liegt auf dem Natur- und Artenschutz. Dazu werden meist über zwei Jahre hinweg Untersuchungen zur Aktivität von Vögeln und Fledermäusen durchgeführt. Die Ergebnisse dienen unter anderem dazu, Abschaltzeiten festzulegen. Diese sorgen dafür, dass Windräder während besonders sensibler Aktivitätszeiten automatisch stillstehen und so der Schutz der Tierwelt gewährleistet wird. Außerdem werden im Zuge der Umweltverträglichkeitsprüfung auch Ausgleichsmaßnahmen festgelegt, wie beispielsweise Aufforstungen oder Aufwertung anderer Lebensräume (Blühflächen oder Habitate für bestimmte Arten).',
					'Repowering: Beim sogenannten Repowering werden alte Windräder durch modernere, leistungsstärkere Windräder ersetzt. Das Land Kärnten hat jedoch für das Repowering außerhalb der Beschleunigungsgebiete eine Erhöhung der Nabenhöhe um maximal 30 % vorgesehen. Diese Regelung betrifft die bestehenden Windkraftanlagen am Plöckenpass, die aufgrund dieser Regelung nicht erneuert werden können, da heute keine Windräder mehr am Markt verkauft werden, die nur 30 % höher sind als die bestehenden.',
					'Erst wenn alle Prüfungen positiv abgeschlossen sind und alle Genehmigungen vorliegen, darf mit dem Bau der Windräder begonnen werden.',
				],
			},
		],
	},

	// Salzburg
	[STATE.SALZBURG]: {
		intro: 'In Salzburg müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Zonierung',
				responsible: 'Land',
				paragraphs: [
					'Salzburg hat im Landesentwicklungsprogramm 2025 einen verbindlichen, landesweiten Planungsrahmen für die Windkraft geschaffen. Kernstück sind 11 ausgewiesene Vorrangzonen für Windenergie: Anzenberg, Rannberg-Ebenholzspitz, Ofenauer Berg, Sulzau, Schneeberg, Hochegg, Hochalm, Resterhöhe-Rossgruberkogel, Windsfeld, Pirkegg, Lehmberg. Diese Zonen wurden in einem mehrstufigen Verfahren unter Einbindung fachlicher Gutachten (Naturschutz, Landschaftsbild, Siedlungs- und Freiraumentwicklung) ermittelt und im Rahmen einer Strategischen Umweltprüfung auf ihre Umweltverträglichkeit hin überprüft.',
					'Diese Zonen gelten als besonders geeignete Flächen, die vorrangig für Windkraft vorgesehen sind. Die restliche Landesfläche wird für Windkraft weder aktiv eingeplant, noch kategorisch ausgeschlossen (= neutrale Zone).',
				],
			},
			{
				number: 2,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KONKRET,
			},
			{
				number: 3,
				title: 'Widmung',
				responsible: 'Gemeinde',
				paragraphs: [
					'Als nächstes muss die Gemeinde die Fläche für die Windräder im örtlichen Flächenwidmungsplan als „Grünland-Windkraftanlagen" ausweisen. Die Widmung wird dabei vom betreffenden Gemeinderat beschlossen. Für die Widmung ist eine Strategische Umweltprüfung des Landes Salzburg notwendig. Diese dient dazu, voraussichtliche Umweltauswirkungen von Plänen und Programmen systematisch zu bewerten, bevor diese beschlossen oder umgesetzt werden.',
				],
			},
			{
				number: 4,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: [
					...UVP_STANDARD.slice(0, 1),
					'Ein besonderer Schwerpunkt liegt auf dem Natur- und Artenschutz. Dazu werden meist über zwei Jahre hinweg Untersuchungen zur Aktivität von Vögeln und Fledermäusen durchgeführt. Die Ergebnisse dienen unter anderem dazu, Abschaltzeiten festzulegen. Diese sorgen dafür, dass Windräder während besonders sensibler Aktivitätszeiten automatisch stillstehen und so der Schutz der Tierwelt gewährleistet wird. Außerdem werden im Zuge der Umweltverträglichkeitsprüfung auch Ausgleichsmaßnahmen festgelegt, wie beispielsweise Aufforstungen oder Aufwertung anderer Lebensräume (Blühflächen oder Habitate für bestimmte Arten). Innerhalb der Vorrangzonen wurden die Minderungsmaßnahmen bereits im Umweltbericht vom Land festgelegt und sind verbindlich. Die Behörden müssen diese Maßnahmen beachten und können nicht davon abweichen, was zum Ziel hat, die Verfahren zu beschleunigen.',
					...UVP_STANDARD.slice(2),
				],
			},
		],
	},

	// Oberösterreich
	[STATE.OBERÖSTERREICH]: {
		intro: 'Grundsätzlich können in Oberösterreich Windkraftprojekte zur Genehmigung eingereicht werden.',
		steps: [
			{
				number: 1,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: [
					'Am Beginn jedes Windkraftprojekts steht die sorgfältige Prüfung eines möglichen Standorts. Dabei wird untersucht, ob ausreichend Wind vorhanden ist, ob der Abstand zum nächsten Siedlungsgebiet ausreichend ist (Mindestabstand zu Wohngebäuden 1 km) und ob ein Anschluss an das Stromnetz technisch möglich ist. Ebenso werden die Zufahrtsmöglichkeiten für Bau und Wartung sowie raumordnungsrechtliche Rahmenbedingungen geprüft (z.B. Hangneigung).',
					'Zeigt diese erste Prüfung, dass ein Standort grundsätzlich geeignet ist, werden die benötigten Grundstücksflächen gesichert. In der Praxis geschieht dies meist über Pachtverträge mit den Grundstückseigentümer:innen.',
					'Dann beginnt die wirtschaftlich-technische Detailprüfung. Dazu werden in der Regel 1 Jahr lang Windmessungen durchgeführt. Aus den Messdaten wird berechnet, wie viel Strom ein Windrad an diesem Standort voraussichtlich erzeugen könnte. Auf dieser Grundlage können Betreiber einschätzen, ob sich das Projekt wirtschaftlich lohnt und welcher Windrad-Typ geeignet ist. Die Windmessung dient ausschließlich der wirtschaftlich-technischen Projektvalidierung und stellt noch keine Genehmigung für den Bau dar.',
					'Auch der Netzanschluss muss geprüft und möglichst frühzeitig gesichert werden, da die verfügbaren Netzkapazitäten begrenzt sind.',
				],
			},
			{
				number: 2,
				title: 'Widmung',
				responsible: 'Gemeinde',
				paragraphs: [
					'Als nächstes müssen die für Windkraftprojekte geeigneten Flächen noch entsprechend umgewidmet werden. Für Windräder gibt es die Sonderwidmung „Grünland – Windkraftanlage". Die Widmung wird dabei vom betreffenden Gemeinderat beschlossen. Für die Widmung ist eine Strategische Umweltprüfung des Landes Oberösterreich notwendig. Diese dient dazu, voraussichtliche Umweltauswirkungen von Plänen und Programmen systematisch zu bewerten, bevor diese beschlossen oder umgesetzt werden.',
					'Hinweis zur Rechtslage: Bei großen Windkraftprojekten (ab 30 MW bzw. ab 15 MW über 1.000 m Seehöhe) reicht unter Umständen auch eine einfache Zustimmung der Gemeinde und die Fläche muss nicht extra gewidmet werden (siehe § 4a Abs 3 UVP-G).',
				],
			},
			{
				number: 3,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: UVP_STANDARD,
			},
		],
	},

	// Burgenland
	[STATE.BURGENLAND]: {
		intro: 'Im Burgenland müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Zonierung',
				responsible: 'Land',
				paragraphs: [
					'Im Burgenland ist der erste Schritt die Frage, ob die geplante Fläche in einer Eignungszone liegt. Nur in solchen Eignungszonen sind Errichtung und Betrieb von Windkraftanlagen zulässig; in Ausschlusszonen ist der Bau von Windkraftanlagen ausgeschlossen.',
					'Die Zonierung wird von der Landesregierung per Verordnung festgelegt und im Raumordnungsrecht abgesichert. Die Zonierungsverordnung unterliegt einer Strategischen Umweltprüfung.',
					'Ein Windrad ist im Burgenland nicht überall möglich, sondern nur dort, wo das Land die Fläche grundsätzlich für Windkraft vorgesehen hat. Es muss grundsätzlich ein Mindestabstand von 1.200 Metern zum nächsten Wohnbauland eingehalten werden.',
				],
			},
			{
				number: 2,
				title: 'Kenntlichmachung im Flächenwidmungsplan',
				responsible: 'Gemeinde',
				paragraphs: [
					'Die Gemeinde muss die Zonierung lediglich im Flächenwidmungsplan ersichtlich machen. Es braucht keine zusätzliche Widmung der Gemeinde.',
				],
			},
			{
				number: 3,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KONKRET,
			},
			{
				number: 4,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: UVP_STANDARD,
			},
		],
	},

	// Wien
	[STATE.WIEN]: {
		intro: 'Da Wien eine dicht besiedelte Stadt ist, sind geeignete Flächen für Windräder sehr begrenzt. Folgende Schritte müssen durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: STANDORTPRUEFUNG_KURZ,
			},
			{
				number: 2,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: UVP_STANDARD,
			},
		],
	},

	// Vorarlberg
	[STATE.VORARLBERG]: {
		intro: 'In Vorarlberg müssen folgende Schritte durchlaufen werden, um ein Windrad errichten zu können:',
		steps: [
			{
				number: 1,
				title: 'Standortprüfung, Flächensicherung & Netzanschlussvertrag',
				responsible: 'Windkraftbetreiber',
				paragraphs: [
					'Am Beginn jedes Windkraftprojekts steht die sorgfältige Prüfung eines möglichen Standorts. Dabei wird untersucht, ob ausreichend Wind vorhanden ist, ob der Abstand zum nächsten Siedlungsgebiet ausreichend ist (abhängig vom Schall, meist ca. 800 - 1.200 m) und ob ein Anschluss an das Stromnetz technisch möglich ist. Ebenso werden die Zufahrtsmöglichkeiten für Bau und Wartung sowie raumordnungsrechtliche Rahmenbedingungen geprüft (z.B. Hangneigung).',
					'Zeigt diese erste Prüfung, dass ein Standort grundsätzlich geeignet ist, werden die benötigten Grundstücksflächen gesichert. In der Praxis geschieht dies meist über Pachtverträge mit den Grundstückseigentümer:innen.',
					'Dann beginnt die wirtschaftlich-technische Detailprüfung. Dazu werden in der Regel 1 Jahr lang Windmessungen durchgeführt. Aus den Messdaten wird berechnet, wie viel Strom ein Windrad an diesem Standort voraussichtlich erzeugen könnte. Auf dieser Grundlage können Betreiber einschätzen, ob sich das Projekt wirtschaftlich lohnt und welcher Windrad-Typ geeignet ist. Die Windmessung dient ausschließlich der wirtschaftlich-technischen Projektvalidierung und stellt noch keine Genehmigung für den Bau dar.',
					'Auch der Netzanschluss muss geprüft und möglichst frühzeitig gesichert werden, da die verfügbaren Netzkapazitäten begrenzt sind.',
				],
			},
			{
				number: 2,
				title: 'Widmung bzw. Zustimmung',
				responsible: 'Gemeinde',
				paragraphs: [
					'Als nächstes müssen die für Windkraftprojekte geeigneten Flächen noch entsprechend umgewidmet werden. Die Widmung wird dabei vom betreffenden Gemeinderat beschlossen. Für die Widmung ist eine Strategische Umweltprüfung des Landes Vorarlberg notwendig. Diese dient dazu, voraussichtliche Umweltauswirkungen von Plänen und Programmen systematisch zu bewerten, bevor diese beschlossen oder umgesetzt werden.',
					'Hinweis zur Rechtslage: Bei großen Windkraftprojekten (ab 30 MW bzw. ab 15 MW über 1.000 m Seehöhe) reicht unter Umständen auch eine einfache Zustimmung der Gemeinde und die Fläche muss nicht extra gewidmet werden (siehe § 4a Abs 3 UVP-G).',
				],
			},
			{
				number: 3,
				title: 'Genehmigungsverfahren: Umweltverträglichkeitsprüfung',
				responsible: 'Land',
				paragraphs: [
					...UVP_STANDARD.slice(0, 2),
					'Eine UVP ist bei Windkraftanlagen mit einer elektrischen Gesamtleistung von mindestens 30 MW erforderlich. Bei Anlagen über 1.000 Meter Seehöhe liegt die Schwelle bei 15 MW.',
					'Erst wenn alle Prüfungen positiv abgeschlossen sind und alle Genehmigungen vorliegen, darf mit dem Bau der Windräder begonnen werden.',
				],
			},
		],
	},
};
