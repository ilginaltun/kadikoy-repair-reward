// useUserPoints.js
import { useState, useEffect } from 'https://esm.sh/preact@10.19.6/hooks';
import { supabase } from './supabaseClient.js';

export function useUserPoints(userId) {
  const [points, setPoints] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!userId) return;

    let isMounted = true;

    // 1. Initial Fetch
    const fetchPoints = async () => {
      try {
        setLoading(true);
        const { data, error: dbError } = await supabase
          .from('profiles')
          .select('total_points')
          .eq('id', userId)
          .single();

        if (dbError) throw dbError;
        
        if (isMounted && data) {
          setPoints(data.total_points);
        }
      } catch (err) {
        if (isMounted) setError(err.message);
      } finally {
        if (isMounted) setLoading(false);
      }
    };

    fetchPoints();

    // 2. Real-time Subscription (Listen for INSERTS to repairs/redemptions via triggers)
    // The trigger automatically updates the 'profiles' row, so we just listen to 'profiles' UPDATE
    const subscription = supabase
      .channel(`profile_points_changes_${userId}`)
      .on(
        'postgres_changes',
        {
          event: 'UPDATE',
          schema: 'public',
          table: 'profiles',
          filter: `id=eq.${userId}`,
        },
        (payload) => {
          if (payload.new && typeof payload.new.total_points === 'number') {
            setPoints(payload.new.total_points);
          }
        }
      )
      .subscribe();

    return () => {
      isMounted = false;
      supabase.removeChannel(subscription);
    };
  }, [userId]);

  // Optionally provide a function to redeem (spend) points directly
  const spendPoints = async (venueName, pointsCost) => {
    if (!userId) return { success: false, error: 'User not logged in' };
    if (points < pointsCost) return { success: false, error: 'Not enough points' };

    try {
      // Because we created a PostgreSQL trigger, inserting into 'redemptions'
      // will automatically deduct points from the profile!
      // This is atomic and safe from race conditions.
      const { data, error: insertError } = await supabase
        .from('redemptions')
        .insert({
          user_id: userId,
          venue_name: venueName,
          points_spent: pointsCost,
        });

      if (insertError) throw insertError;
      return { success: true, data };
    } catch (err) {
      return { success: false, error: err.message };
    }
  };

  return { points, loading, error, spendPoints };
}
