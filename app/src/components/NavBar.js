import React from "react"
import { AppBar, Toolbar, Typography } from "@mui/material"
import SideBar from "./SideBar"

export default function NavBar() {
  return (
    <AppBar position='fixed' sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
      <Toolbar>
        <SideBar />
        <Typography variant='h6' noWrap component="div">
          Purchase Order Tool
        </Typography>
      </Toolbar>
    </AppBar>
  )
}