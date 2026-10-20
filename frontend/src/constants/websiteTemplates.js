export const WEBSITE_TEMPLATES = {
  restaurant: [
    ["restaurant_classic", "Classic bistro", "A photo led dining page with a warm reservation feel."],
    ["restaurant_modern", "Modern menu", "A clean, spacious layout focused on menu choices."],
    ["restaurant_bistro", "Neighborhood bistro", "A cozy, intimate layout for local dining."],
    ["restaurant_market", "Market table", "A colorful, lively layout for cafes and casual dining."],
  ],
  salon: [
    ["salon_editorial", "Editorial studio", "A refined split layout for a premium salon."],
    ["salon_minimal", "Minimal studio", "A clean, image forward layout with generous space."],
    ["salon_botanical", "Botanical beauty", "A natural layout with soft shapes and earthy details."],
    ["salon_glam", "Glam lounge", "A dramatic, high contrast layout with a polished feel."],
  ],
  clinic: [
    ["clinic_calm", "Calm care", "A centered, reassuring layout with a quiet feel."],
    ["clinic_modern", "Modern practice", "A crisp, information forward healthcare layout."],
    ["clinic_family", "Family clinic", "A friendly layout with approachable cards and clear steps."],
    ["clinic_holistic", "Holistic wellness", "A softer, nature inspired layout for wellness care."],
  ],
  sports_turf: [
    ["sports_arena", "Arena", "A bold field banner with high energy booking cards."],
    ["sports_club", "Sports club", "A structured club layout for teams and regular players."],
    ["sports_field", "Open field", "An airy outdoor layout centered on the playing space."],
    ["sports_night", "Night game", "A dark, vivid layout for evening games and events."],
  ],
};

export function normalizeBusinessType(type) {
  const value = String(type || "").trim().toLowerCase().replace(/[&_-]+/g, " ");
  if (value.includes("restaurant") || value.includes("cafe") || value.includes("dining")) return "restaurant";
  if (value.includes("salon") || value.includes("beauty")) return "salon";
  if (value.includes("clinic") || value.includes("dental") || value.includes("health")) return "clinic";
  if (value.includes("sport") || value.includes("turf") || value.includes("football") || value.includes("field")) return "sports_turf";
  return value;
}

export function templatesForBusiness(type) {
  return WEBSITE_TEMPLATES[normalizeBusinessType(type)] || [];
}
