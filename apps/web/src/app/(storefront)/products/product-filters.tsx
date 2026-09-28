"use client";

import { useState, type FormEvent } from "react";
import { useDictionary } from "@/i18n/dictionary-context";
import { TextField, CheckboxField, Button } from "@/components/ui";
import type { ProductListParams } from "@/lib/api/catalog";
import styles from "./page.module.css";

export type FilterFormValues = Pick<
  ProductListParams,
  "q" | "price_min" | "price_max" | "material" | "availability" | "featured"
>;

export function ProductFilters({
  initial,
  onApply,
}: {
  initial: FilterFormValues;
  onApply: (values: FilterFormValues) => void;
}) {
  const { dict } = useDictionary();
  const t = dict.catalog.filters;

  const [q, setQ] = useState(initial.q ?? "");
  const [priceMin, setPriceMin] = useState(
    initial.price_min !== undefined ? String(initial.price_min) : "",
  );
  const [priceMax, setPriceMax] = useState(
    initial.price_max !== undefined ? String(initial.price_max) : "",
  );
  const [material, setMaterial] = useState(initial.material ?? "");
  const [inStockOnly, setInStockOnly] = useState(
    initial.availability === "in_stock",
  );
  const [featuredOnly, setFeaturedOnly] = useState(initial.featured === true);

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    onApply({
      q: q.trim() || undefined,
      price_min: priceMin ? Number(priceMin) : undefined,
      price_max: priceMax ? Number(priceMax) : undefined,
      material: material.trim() || undefined,
      availability: inStockOnly ? "in_stock" : "all",
      featured: featuredOnly ? true : undefined,
    });
  }

  function handleClear() {
    setQ("");
    setPriceMin("");
    setPriceMax("");
    setMaterial("");
    setInStockOnly(false);
    setFeaturedOnly(false);
    onApply({});
  }

  return (
    <form className={styles.filterGroup} onSubmit={handleSubmit}>
      <span className={styles.filterHeading}>{t.heading}</span>

      <TextField
        label={t.searchLabel}
        value={q}
        onChange={(e) => setQ(e.target.value)}
      />

      <div className={styles.priceRow}>
        <TextField
          label={t.priceMinLabel}
          type="number"
          min={0}
          inputMode="decimal"
          value={priceMin}
          onChange={(e) => setPriceMin(e.target.value)}
        />
        <TextField
          label={t.priceMaxLabel}
          type="number"
          min={0}
          inputMode="decimal"
          value={priceMax}
          onChange={(e) => setPriceMax(e.target.value)}
        />
      </div>

      <TextField
        label={t.materialLabel}
        placeholder={t.materialPlaceholder}
        value={material}
        onChange={(e) => setMaterial(e.target.value)}
      />

      <CheckboxField
        label={t.inStockOnlyLabel}
        checked={inStockOnly}
        onChange={(e) => setInStockOnly(e.target.checked)}
      />
      <CheckboxField
        label={t.featuredOnlyLabel}
        checked={featuredOnly}
        onChange={(e) => setFeaturedOnly(e.target.checked)}
      />

      <div style={{ display: "flex", gap: "0.5rem" }}>
        <Button type="submit" variant="primary" size="sm">
          {t.applyButton}
        </Button>
        <Button type="button" variant="ghost" size="sm" onClick={handleClear}>
          {t.clearButton}
        </Button>
      </div>
    </form>
  );
}
