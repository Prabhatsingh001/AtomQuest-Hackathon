import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function computeScore(
  uomType: string,
  target: number | null,
  actual: number | null,
  targetDate?: string | null,
  completionDate?: string | null
): number {
  if (uomType === 'min') {
    if (!target || target === 0) return 0;
    if (actual === null || actual === undefined) return 0;
    return Math.min(actual / target, 1.0);
  }
  if (uomType === 'max') {
    if (actual === null || actual === undefined || actual === 0) return 1.0;
    if (!target) return 0;
    return Math.min(target / actual, 1.0);
  }
  if (uomType === 'zero') {
    if (actual === null || actual === undefined) return 0;
    return actual === 0 ? 1.0 : 0;
  }
  if (uomType === 'timeline') {
    if (completionDate && targetDate) {
      return new Date(completionDate) <= new Date(targetDate) ? 1.0 : 0.5;
    }
    return 0;
  }
  return 0;
}

export const THRUST_AREAS = [
  'Revenue Growth',
  'Customer Satisfaction',
  'Cost Optimization',
  'Process Improvement',
  'Compliance',
  'Product Development',
  'Quality',
  'Team Development',
  'Innovation',
  'Company Culture',
];
