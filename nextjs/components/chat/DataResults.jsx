import {Stack} from "@mantine/core";
import React from "react";

import TableResult from "./TableResult";

function DataResults({dataResponse}) {
  const {data} = dataResponse;
  return (
    <Stack mt="md">
      <TableResult data={data} />
      {/* <VizResult cube={cube} dataset={data} params={params} /> */}
    </Stack>
  );
}

export default DataResults;
