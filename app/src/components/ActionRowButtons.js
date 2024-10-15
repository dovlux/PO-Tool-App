import { Stack } from "@mui/material";
import { useState } from "react";
import DeletePoDialog from "./DeletePoDialog";
import CreateBreakdownDialog from "./CreateBreakdownDialog";

export default function ActionRowButtons ({ row, addSnackbar, fetchPos }) {
  const [buttonLoading, setButtonLoading] = useState(false);

  return (
    <Stack direction='row' alignContent='center' spacing={1} m={1}>
      {(
        row.status === "Worksheet Created" || row.status === "Errors in worksheet (Breakdown)"
      ) && (
        <DeletePoDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
      {(
        row.is_ats === false &&
        (row.status === "Worksheet Created" ||
        row.status === "Errors in worksheet (Breakdown)")
      ) && (
        <CreateBreakdownDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
    </Stack>
  )
}