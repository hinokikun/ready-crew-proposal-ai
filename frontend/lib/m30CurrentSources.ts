import type { M30CurrentSourceDto } from "@/types/m30Api";
import {
  M30_PRODUCT_SOURCE_IDENTITIES,
  M30_PRODUCT_SOURCE_IDENTITY_ORDER,
  type ProductSourceField,
} from "@/types/m30ProductSourceIdentity";

export type M30CurrentProductValues = Readonly<Record<ProductSourceField, string>>;

export function buildM30CurrentSources(values: M30CurrentProductValues): M30CurrentSourceDto[] {
  return M30_PRODUCT_SOURCE_IDENTITY_ORDER.flatMap((field) => {
    const value = values[field];
    if (typeof value !== "string" || !value.trim()) return [];
    const identity = M30_PRODUCT_SOURCE_IDENTITIES[field];
    return [{
      source_id: identity.source_id,
      source_field: identity.source_field,
      value,
      source_reference: identity.source_reference,
    }];
  });
}
