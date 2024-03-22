CREATE OR REPLACE FUNCTION public.match_table(query_embedding vector, similarity_threshold double precision, match_count integer)
 RETURNS TABLE(table_name text, similarity double precision)
 LANGUAGE plpgsql
AS $function$
begin
  return query
  select
    cubes.table_name,
    1 - (cubes.embedding <=> query_embedding) as similarity
  from datausa_tables.cubes
  where 1 - (cubes.embedding <=> query_embedding) > similarity_threshold
  order by cubes.embedding <=> query_embedding
  limit match_count;
end;
$function$
;
