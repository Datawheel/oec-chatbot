CREATE OR REPLACE FUNCTION public.match_drilldowns(query_embedding vector, similarity_threshold double precision, match_count integer, table_name text, drilldown_names text[])
 RETURNS TABLE(drilldown_id text, drilldown_name text, similarity double precision)
 LANGUAGE plpgsql
AS $function$
BEGIN
  RETURN QUERY
  select
    drilldowns.drilldown_id,
    drilldowns.drilldown,
    1 - (drilldowns.embedding <=> query_embedding) AS similarity
  FROM datasaudi_drilldowns.drilldowns
  WHERE drilldowns.cube_name = table_name
    AND drilldowns.drilldown = ANY(drilldown_names)
    AND 1 - (drilldowns.embedding <=> query_embedding) > similarity_threshold
  ORDER BY drilldowns.embedding <=> query_embedding
  LIMIT match_count;
END;
$function$
;
