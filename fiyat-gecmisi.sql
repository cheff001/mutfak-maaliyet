-- Mutfak Maliyet: gerçek fiyat geçmişi
-- Supabase > SQL Editor'de tamamını bir kerede çalıştır.

-- 1. Günlük fiyat kayıtları
create table if not exists public.price_history (
  ingredient text not null,
  day date not null,
  hal numeric,
  metro numeric,
  market numeric,
  primary key (ingredient, day)
);

alter table public.price_history enable row level security;

drop policy if exists "giris yapanlar okuyabilir" on public.price_history;
create policy "giris yapanlar okuyabilir" on public.price_history
  for select to authenticated using (true);
-- insert/update/delete için policy yok: istemci yazamaz, sadece aşağıdaki zamanlı görev yazar.

-- 2. Her ürün için son 180 gün içindeki en eski kayıt (karşılaştırma tabanı)
create or replace view public.price_baseline
with (security_invoker = true) as
select distinct on (ingredient) ingredient, day, hal, metro, market
from public.price_history
where day >= current_date - 180
order by ingredient, day;

grant select on public.price_baseline to authenticated;

-- 3. Anlık görüntü fonksiyonu (bugünün fiyatlarını kaydeder, gün içinde tekrar çalışırsa günceller)
create or replace function public.snapshot_prices() returns void
language sql security definer set search_path = public as $$
  insert into public.price_history (ingredient, day, hal, metro, market)
  select ingredient, current_date, hal, metro, market from public.prices
  on conflict (ingredient, day) do update
    set hal = excluded.hal, metro = excluded.metro, market = excluded.market;
$$;
revoke all on function public.snapshot_prices() from public, anon, authenticated;

-- 4. İlk kaydı hemen al
select public.snapshot_prices();

-- 5. Her gün 20:00 UTC (23:00 Türkiye) otomatik çalışsın
create extension if not exists pg_cron;
select cron.schedule('fiyat-gecmisi-gunluk', '0 20 * * *', $$select public.snapshot_prices()$$);
