-- Girişsiz demo için: fiyat listesini giriş yapmamış ziyaretçilerin de okumasına izin verir.
-- Sadece "prices" tablosunu açar. Kullanıcı verileri (tarifler, işletmeler, favoriler) kapalı kalır.
-- Yazma yetkisi verilmez.
drop policy if exists "demo icin anonim fiyat oku" on public.prices;
create policy "demo icin anonim fiyat oku" on public.prices
  for select to anon using (true);
grant select on public.prices to anon;
