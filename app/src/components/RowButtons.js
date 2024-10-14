import { Stack } from "@mui/material";
import { useState } from "react";
import DeletePoDialog from "./DeletePoDialog";
import CreateBreakdownDialog from "./CreateBreakdownDialog";

export default function RowButtons ({ row }) {
  const [buttonLoading, setButtonLoading] = useState(false);

  return (
    <>
      {(row.status === "Worksheet Created") && (
        <Stack direction='row' alignContent='center' spacing={1} m={1}>
          <CreateBreakdownDialog
            buttonLoading={buttonLoading}
            setButtonLoading={setButtonLoading}
            id={row.id}
          />
          <DeletePoDialog
            buttonLoading={buttonLoading}
            setButtonLoading={setButtonLoading}
            id={row.id}
          />
        </Stack>
      )}
    </>
  )
}