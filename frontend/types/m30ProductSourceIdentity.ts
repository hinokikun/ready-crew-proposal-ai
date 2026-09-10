/** Stable Product source identities for the M30 V1 cross-boundary contract. */

export type ProductSourceField =
  | "project_brief"
  | "decisionMaker"
  | "accountableOwner"
  | "preparationAnalysis"
  | "evidence";

export type ProductSourceIdentity = {
  readonly source_id: string;
  readonly source_field: string;
  readonly source_reference: string;
};

export const M30_PRODUCT_SOURCE_IDENTITY_ORDER = [
  "project_brief",
  "decisionMaker",
  "accountableOwner",
  "preparationAnalysis",
  "evidence"
] as const satisfies readonly ProductSourceField[];

export const M30_PRODUCT_SOURCE_IDENTITIES: Readonly<Record<ProductSourceField, ProductSourceIdentity>> = {
  project_brief: {
    source_id: "product.step1.project_brief",
    source_field: "project_brief",
    source_reference: "Step1.project_brief"
  },
  decisionMaker: {
    source_id: "product.step1.decision_maker",
    source_field: "Step1.decisionMaker",
    source_reference: "Step1.decisionMaker"
  },
  accountableOwner: {
    source_id: "product.step1.accountable_owner",
    source_field: "Step1.accountableOwner",
    source_reference: "Step1.accountableOwner"
  },
  preparationAnalysis: {
    source_id: "product.step1.preparation_analysis",
    source_field: "Step1.preparationAnalysis",
    source_reference: "Step1.preparationAnalysis"
  },
  evidence: {
    source_id: "product.step1.evidence",
    source_field: "Step1.evidence",
    source_reference: "Step1.evidence"
  }
};
