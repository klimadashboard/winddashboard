export type SettlementVariant = "default" | "800" | "1000" | "1200" | "1500" | "2000";

export interface SettlementVariantDef {
	id: SettlementVariant;
	label: string;
	meters: number | null; // null = Bundesland-specific ("default")
}

// The 6 settlement-distance scenarios embedded in the source raster (see
// SETTLEMENT_BUFFER_VARIANTS tag / PIPELINE.md). "default" applies the
// Bundesland-specific legal minimum distances (1.000–1.500 m); the rest are a
// single uniform distance nationwide, for comparison.
export const SETTLEMENT_VARIANTS: SettlementVariantDef[] = [
	{ id: "800", label: "800 m", meters: 800 },
	{ id: "1000", label: "1.000 m", meters: 1000 },
	{ id: "1200", label: "1.200 m", meters: 1200 },
	{ id: "default", label: "Gesetzlich (bundeslandspezifisch)", meters: null },
	{ id: "1500", label: "1.500 m", meters: 1500 },
	{ id: "2000", label: "2.000 m", meters: 2000 },
];

export function settlementVariantDef(id: SettlementVariant): SettlementVariantDef {
	return SETTLEMENT_VARIANTS.find((v) => v.id === id) ?? SETTLEMENT_VARIANTS[0];
}

export function possibleZonesUrl(variant: SettlementVariant): string {
	return `/data/possible_zones_${variant}`;
}

export function zoneCentroidsUrl(variant: SettlementVariant): string {
	return `/data/zone_centroids_${variant}`;
}
