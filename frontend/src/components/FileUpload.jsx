import React, { useState, useCallback } from 'react';
import { useDropzone } from 'react-dropzone';
import { Button } from '@/components/ui/button';
import { Upload, File, X } from 'lucide-react';

const FileUpload = ({ onFileUpload }) => {
  const [file, setFile] = useState(null);

  const onDrop = useCallback((acceptedFiles) => {
    if (acceptedFiles && acceptedFiles.length > 0) {
      setFile(acceptedFiles[0]);
      onFileUpload(acceptedFiles[0]);
    }
  }, [onFileUpload]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx']
    },
    multiple: false
  });

  const removeFile = () => {
    setFile(null);
    onFileUpload(null);
  };

  return (
    <div className="mt-4">
      <label className="block text-lg font-bold text-gray-500 mb-2">
        자기소개서 업로드
      </label>
      <div
        {...getRootProps()}
        className={`p-4 border-2 border-dashed rounded-md text-center cursor-pointer transition-colors ${
          isDragActive ? 'border-blue-400 bg-blue-50' : 'border-gray-300 hover:border-blue-400'
        }`}
      >
        <input {...getInputProps()} />
        {file ? (
          <div className="flex items-center justify-between bg-gray-100 p-2 rounded">
            <div className="flex items-center">
              <File className="mr-2 h-5 w-5 text-blue-500" />
              <span className="text-sm text-gray-700">{file.name}</span>
            </div>
            <Button
              type="button"
              variant="ghost"
              size="sm"
              onClick={(e) => {
                e.stopPropagation();
                removeFile();
              }}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <div>
            <Upload className="mx-auto h-12 w-12 text-gray-400" />
            <p className="mt-2 text-sm text-gray-600">
              파일을 드래그하여 업로드하거나 클릭하여 파일을 선택하세요
            </p>
            <p className="mt-1 text-xs text-gray-500">
              PDF, DOC, DOCX 파일 (최대 10MB)
            </p>
          </div>
        )}
      </div>
    </div>
  );
};

export default FileUpload;