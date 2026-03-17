import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const publicApiBase = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
const internalApiBase = process.env.DATA_FORGE_API_INTERNAL_URL;

export const API_BASE =
  typeof window === "undefined" ? internalApiBase || publicApiBase : "";
