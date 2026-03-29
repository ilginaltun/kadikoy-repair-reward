// supabaseClient.js
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2.39.3';

// Replace these with your actual Supabase project credentials.
// You can find them in your Supabase Dashboard under Settings > API.
const SUPABASE_URL = 'https://replace-me.supabase.co';
const SUPABASE_ANON_KEY = 'replace-this-with-anon-key';

let client;
try {
    client = createClient(SUPABASE_URL, SUPABASE_ANON_KEY);
} catch (e) {
    console.error("Supabase config error:", e);
    client = { 
       from: () => ({ insert: async () => { throw new Error("Supabase is not configured.") } })
    };
}
export const supabase = client;
