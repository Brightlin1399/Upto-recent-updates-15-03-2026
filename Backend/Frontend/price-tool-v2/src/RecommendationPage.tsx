import { useState } from "react";
import React, { useRef, useEffect } from 'react';
import { Bold, Italic, Underline, Strikethrough, List, ListOrdered, AlignLeft, AlignCenter, AlignRight, Link, Image, Type } from 'lucide-react';

const RichTextEditor = () => {
  const [content, setContent] = useState('');
  const [fontSize, setFontSize] = useState('12');
  const [fontFamily, setFontFamily] = useState('Salesforce Sans');
  const editorRef = useRef(null);

  const fonts = [
    'Salesforce Sans',
    'Arial',
    'Times New Roman',
    'Courier New',
    'Georgia',
    'Verdana'
  ];

  const fontSizes = ['8', '10', '12', '14', '16', '18', '20', '24', '28', '32'];

  const execCommand = (command, value = null) => {
    document.execCommand(command, false, value);
    editorRef.current?.focus();
  };

  const handleFontFamily = (font) => {
    setFontFamily(font);
    execCommand('fontName', font);
  };

  const handleFontSize = (size) => {
    setFontSize(size);
    execCommand('fontSize', '3');
    const fontElements = editorRef.current?.querySelectorAll('font[size="3"]');
    fontElements?.forEach(element => {
      element.removeAttribute('size');
      element.style.fontSize = `${size}px`;
    });
  };

  const handleLink = () => {
    const url = prompt('Enter URL:');
    if (url) {
      execCommand('createLink', url);
    }
  };

  const handleImage = () => {
    const url = prompt('Enter image URL:');
    if (url) {
      execCommand('insertImage', url);
    }
  };

  const handleInput = () => {
    setContent(editorRef.current?.innerHTML || '');
  };

  useEffect(() => {
    if (editorRef.current) {
      editorRef.current.style.fontFamily = fontFamily;
      editorRef.current.style.fontSize = `${fontSize}px`;
    }
  }, []);

  const ToolbarButton = ({ onClick, icon: Icon, title }) => (
    <button
      type="button"
      onClick={onClick}
      className="p-2 hover:bg-gray-100 rounded transition-colors"
      title={title}
    >
      <Icon size={18} className="text-gray-700" />
    </button>
  );

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="border-b border-gray-200 p-4">
          <h2 className="text-lg font-semibold text-gray-800 mb-4">Submission Context</h2>
          
          {/* Toolbar */}
          <div className="flex flex-wrap items-center gap-2 p-3 bg-gray-50 border border-gray-300 rounded">
            {/* Font Family Dropdown */}
            <select
              value={fontFamily}
              onChange={(e) => handleFontFamily(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {fonts.map(font => (
                <option key={font} value={font}>{font}</option>
              ))}
            </select>

            {/* Font Size Dropdown */}
            <select
              value={fontSize}
              onChange={(e) => handleFontSize(e.target.value)}
              className="px-3 py-1.5 border border-gray-300 rounded bg-white text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {fontSizes.map(size => (
                <option key={size} value={size}>{size}</option>
              ))}
            </select>

            {/* Divider */}
            <div className="w-px h-6 bg-gray-300 mx-1" />

            {/* Text Color */}
            <input
              type="color"
              onChange={(e) => execCommand('foreColor', e.target.value)}
              className="w-8 h-8 border border-gray-300 rounded cursor-pointer"
              title="Text Color"
            />

            {/* Divider */}
            <div className="w-px h-6 bg-gray-300 mx-1" />

            {/* Formatting Buttons */}
            <ToolbarButton onClick={() => execCommand('bold')} icon={Bold} title="Bold" />
            <ToolbarButton onClick={() => execCommand('italic')} icon={Italic} title="Italic" />
            <ToolbarButton onClick={() => execCommand('underline')} icon={Underline} title="Underline" />
            <ToolbarButton onClick={() => execCommand('strikeThrough')} icon={Strikethrough} title="Strikethrough" />

            {/* Divider */}
            <div className="w-px h-6 bg-gray-300 mx-1" />

            {/* Lists */}
            <ToolbarButton onClick={() => execCommand('insertUnorderedList')} icon={List} title="Bullet List" />
            <ToolbarButton onClick={() => execCommand('insertOrderedList')} icon={ListOrdered} title="Numbered List" />
            <ToolbarButton onClick={() => execCommand('indent')} icon={Type} title="Indent" />
            <ToolbarButton onClick={() => execCommand('outdent')} icon={Type} title="Outdent" />

            {/* Divider */}
            <div className="w-px h-6 bg-gray-300 mx-1" />

            {/* Alignment */}
            <ToolbarButton onClick={() => execCommand('justifyLeft')} icon={AlignLeft} title="Align Left" />
            <ToolbarButton onClick={() => execCommand('justifyCenter')} icon={AlignCenter} title="Align Center" />
            <ToolbarButton onClick={() => execCommand('justifyRight')} icon={AlignRight} title="Align Right" />

            {/* Divider */}
            <div className="w-px h-6 bg-gray-300 mx-1" />

            {/* Insert Link & Image */}
            <ToolbarButton onClick={handleLink} icon={Link} title="Insert Link" />
            <ToolbarButton onClick={handleImage} icon={Image} title="Insert Image" />
          </div>
        </div>

        {/* Editor Area */}
        <div className="p-4">
          <div
            ref={editorRef}
            contentEditable
            onInput={handleInput}
            className="min-h-[200px] p-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-blue-500 bg-white"
            style={{ fontFamily, fontSize: `${fontSize}px` }}
            placeholder="Enter Submission Context"
          />
        </div>

        {/* Character Count */}
        <div className="px-4 pb-4">
          <div className="flex items-center text-gray-500 text-sm">
            <span className="mr-2">◄</span>
            <span>Characters: {content.replace(/<[^>]*>/g, '').length}</span>
          </div>
        </div>
      </div>
    </div>
  );
};









const RecommendationPage = () => {
    return(
        <div>
            <RichTextEditor/>
            
        </div>
    )
}

export default RecommendationPage