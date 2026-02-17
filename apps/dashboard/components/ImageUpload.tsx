/**
 * ImageUpload Component
 * 
 * Drag-and-drop image upload for site evidence.
 * Part of the AgentTheater visual evidence workflow.
 */

import React, { useState, useCallback } from 'react';

interface ImageUploadProps {
  onUpload: (file: File) => void;
  onSkip: () => void;
  siteId: string;
}

export const ImageUpload: React.FC<ImageUploadProps> = ({
  onUpload,
  onSkip,
  siteId
}) => {
  const [isDragging, setIsDragging] = useState(false);
  const [preview, setPreview] = useState<string | null>(null);
  const [fileName, setFileName] = useState<string>('');

  const handleDragEnter = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
  }, []);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragging(false);

    const files = Array.from(e.dataTransfer.files);
    const imageFile = files.find(file => file.type.startsWith('image/'));

    if (imageFile) {
      processFile(imageFile);
    }
  }, []);

  const handleFileInput = useCallback((e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files[0]) {
      processFile(files[0]);
    }
  }, []);

  const processFile = (file: File) => {
    setFileName(file.name);

    // Create preview
    const reader = new FileReader();
    reader.onload = (e) => {
      setPreview(e.target?.result as string);
    };
    reader.readAsDataURL(file);

    // Trigger upload
    onUpload(file);
  };

  return (
    <div className="image-upload">
      <h3>📸 Site Evidence Upload</h3>
      <p className="subtitle">Upload construction site photo for AI analysis</p>

      <div
        className={`dropzone ${isDragging ? 'dropzone--active' : ''} ${preview ? 'dropzone--uploaded' : ''}`}
        onDragEnter={handleDragEnter}
        onDragLeave={handleDragLeave}
        onDragOver={handleDragOver}
        onDrop={handleDrop}
      >
        {preview ? (
          <div className="preview">
            <img src={preview} alt="Site evidence preview" />
            <div className="preview-overlay">
              <span className="file-name">{fileName}</span>
              <button
                className="btn btn-secondary"
                onClick={() => {
                  setPreview(null);
                  setFileName('');
                }}
              >
                Remove
              </button>
            </div>
          </div>
        ) : (
          <div className="dropzone-content">
            <div className="upload-icon">📤</div>
            <p className="primary-text">Drag & drop site photo here</p>
            <p className="secondary-text">or click to browse</p>
            <input
              type="file"
              accept="image/*"
              onChange={handleFileInput}
              className="file-input"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="btn btn-primary">
              Choose File
            </label>
          </div>
        )}
      </div>

      <div className="actions">
        <button
          className="btn btn-outline"
          onClick={onSkip}
          disabled={!!preview}
        >
          Skip Vision Analysis →
        </button>
        <p className="info-text">
          ✅ Graceful degradation: Pipeline continues without vision if skipped
        </p>
      </div>

      <style jsx>{`
        .image-upload {
          background: #2a2a3e;
          padding: 1.5rem;
          border-radius: 8px;
        }

        .image-upload h3 {
          margin: 0 0 0.5rem 0;
        }

        .subtitle {
          margin: 0 0 1rem 0;
          color: #aaa;
          font-size: 0.9rem;
        }

        .dropzone {
          border: 2px dashed #555;
          border-radius: 8px;
          padding: 2rem;
          text-align: center;
          background: #1a1a2e;
          transition: all 0.3s ease;
          cursor: pointer;
          min-height: 200px;
          display: flex;
          align-items: center;
          justify-content: center;
        }

        .dropzone--active {
          border-color: #00d9ff;
          background: rgba(0, 217, 255, 0.1);
        }

        .dropzone--uploaded {
          padding: 0;
        }

        .dropzone-content {
          width: 100%;
        }

        .upload-icon {
          font-size: 3rem;
          margin-bottom: 1rem;
        }

        .primary-text {
          font-size: 1.1rem;
          margin: 0 0 0.5rem 0;
        }

        .secondary-text {
          color: #888;
          margin: 0 0 1.5rem 0;
        }

        .file-input {
          display: none;
        }

        .preview {
          position: relative;
          width: 100%;
          height: 300px;
          border-radius: 8px;
          overflow: hidden;
        }

        .preview img {
          width: 100%;
          height: 100%;
          object-fit: cover;
        }

        .preview-overlay {
          position: absolute;
          bottom: 0;
          left: 0;
          right: 0;
          background: linear-gradient(to top, rgba(0,0,0,0.9), transparent);
          padding: 1rem;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .file-name {
          color: #fff;
          font-size: 0.9rem;
        }

        .btn {
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 6px;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.2s ease;
          font-weight: 500;
        }

        .btn-primary {
          background: #00d9ff;
          color: #000;
        }

        .btn-primary:hover {
          background: #00b8d4;
          transform: translateY(-2px);
        }

        .btn-secondary {
          background: #ff4444;
          color: #fff;
        }

        .btn-secondary:hover {
          background: #cc0000;
        }

        .btn-outline {
          background: transparent;
          border: 1px solid #555;
          color: #aaa;
        }

        .btn-outline:hover:not(:disabled) {
          border-color: #00d9ff;
          color: #00d9ff;
        }

        .btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .actions {
          margin-top: 1.5rem;
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .info-text {
          margin: 0;
          font-size: 0.85rem;
          color: #00ff88;
          text-align: center;
        }
      `}</style>
    </div>
  );
};

export default ImageUpload;
