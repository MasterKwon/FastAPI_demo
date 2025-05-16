import React from 'react';
import { Typography, Box } from '@mui/material';

export const About: React.FC = () => {
  return (
    <Box>
      <Typography variant="h4" component="h1" gutterBottom>
        About
      </Typography>
      <Typography variant="body1" paragraph>
        This is a demo application that showcases the integration of FastAPI backend with React frontend.
      </Typography>
      <Typography variant="body1">
        Built with modern web technologies and best practices.
      </Typography>
    </Box>
  );
}; 