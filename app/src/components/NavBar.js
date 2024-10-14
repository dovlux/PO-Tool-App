import React from "react"
import { AppBar, Toolbar, Typography } from "@mui/material"
import SideBar from "./SideBar"
import { useAllContext } from "./Context"

export default function NavBar() {
  const { roles } = useAllContext();
  
  return (
    <AppBar position='fixed' sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <SideBar roles={roles}/>
        <Typography variant='h6' noWrap component="div">
          Purchase Order Tool
        </Typography>
      </Toolbar>
    </AppBar>
  )
}