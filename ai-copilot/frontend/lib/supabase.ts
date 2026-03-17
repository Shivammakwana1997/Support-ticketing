import { createBrowserClient } from "@supabase/ssr";

/**
 * Create a Supabase client for browser/SSR usage.
 * Use this in client components and API routes.
 * 
 * @example
 * // In a client component:
 * import { createClient } from '@/lib/supabase'
 * 
 * const supabase = createClient()
 * const { data, error } = await supabase.from('users').select('*')
 */
export function createClient() {
  return createBrowserClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!
  );
}

/**
 * Supabase client types for TypeScript
 */
export type SupabaseClient = ReturnType<typeof createClient>;