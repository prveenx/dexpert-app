// ── @dexpert/ui ────────────────────────────────────────
// Design system. Primitive + compound components.
// Zero business logic. Zero API calls. Zero Electron coupling.
// ───────────────────────────────────────────────────────

// ── Components ────────────────────────────────────────
export { Button, type ButtonProps } from './components/button';
export { Input, type InputProps } from './components/input';
export { Textarea, type TextareaProps } from './components/textarea';
export { Label, type LabelProps } from './components/label';
export { Badge, type BadgeProps } from './components/badge';
export { Separator } from './components/separator';
export { Skeleton } from './components/skeleton';
export { Spinner, type SpinnerProps } from './components/spinner';

// ── Compound ──────────────────────────────────────────
export { Card, CardHeader, CardContent, CardFooter } from './compound/card';
export { ScrollArea } from './compound/scroll-area';

// ── Tokens ────────────────────────────────────────────
export { colors } from './tokens/colors';
export { typography } from './tokens/typography';
export { spacing } from './tokens/spacing';

// ── Hooks ─────────────────────────────────────────────
export { useMediaQuery } from './hooks/use-media-query';
export { useDebounce } from './hooks/use-debounce';

// ── Utilities ─────────────────────────────────────────
export { cn } from './utils/cn';
