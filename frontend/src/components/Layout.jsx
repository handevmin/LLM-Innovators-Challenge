import React from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const Layout = ({ children, title }) => {
  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-6 flex flex-col justify-center items-center">
      <Card className="w-full max-w-2xl shadow-lg rounded-2xl overflow-hidden">
        <CardHeader className="bg-blue-500 text-white py-6">
          <CardTitle className="text-3xl font-bold text-center">{title}</CardTitle>
        </CardHeader>
        <CardContent className="p-8">
          {children}
        </CardContent>
      </Card>
    </div>
  );
};

export default Layout;