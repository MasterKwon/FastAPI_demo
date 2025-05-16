import React from 'react';
import { Typography, Box } from '@mui/material';

export const Home: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        Welcome to FastAPI Demo
      </Typography>
      <Typography variant="body1">
        This is a demo application built with FastAPI and React.
      </Typography>
    </Box>
  );
}; 