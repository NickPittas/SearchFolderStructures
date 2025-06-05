#!/usr/bin/env node

/**
 * Filesystem MCP Server
 * Implements Model Context Protocol (MCP) for filesystem operations.
 * 
 * Features:
 * - Read/write files
 * - Create/list/delete directories
 * - Move files/directories
 * - Search files
 * - Get file metadata
 */

import { Server } from "@modelcontextprotocol/sdk/server/index.js";
import { StdioServerTransport } from "@modelcontextprotocol/sdk/server/stdio.js";
import {
  CallToolRequestSchema,
  ListResourcesRequestSchema,
  ListToolsRequestSchema,
  ReadResourceRequestSchema,
  ErrorCode,
  McpError
} from "@modelcontextprotocol/sdk/types.js";
import * as fs from 'fs/promises';
import * as path from 'path';
import { existsSync } from 'fs';
import { glob } from 'glob';

// Get allowed directories from command line arguments
const allowedDirectories = process.argv.slice(2).map(dir => path.resolve(dir));

if (allowedDirectories.length === 0) {
  console.error("Error: No allowed directories specified");
  console.error("Usage: npx @modelcontextprotocol/server-filesystem <directory1> <directory2> ...");
  process.exit(1);
}

// Validate that all directories exist
for (const dir of allowedDirectories) {
  try {
    const stat = await fs.stat(dir);
    if (!stat.isDirectory()) {
      console.error(`Error: ${dir} is not a directory`);
      process.exit(1);
    }
  } catch (error) {
    console.error(`Error: Directory ${dir} does not exist`);
    process.exit(1);
  }
}

/**
 * Check if a path is within allowed directories
 */
function isPathAllowed(filePath: string): boolean {
  const resolvedPath = path.resolve(filePath);
  return allowedDirectories.some(dir => resolvedPath.startsWith(dir));
}

/**
 * Create an MCP server with capabilities for filesystem operations
 */
const server = new Server(
  {
    name: "filesystem-server",
    version: "0.1.0",
  },
  {
    capabilities: {
      resources: {},
      tools: {},
    },
  }
);

/**
 * Handler for listing available resources
 * Exposes a single system resource for file operations
 */
server.setRequestHandler(ListResourcesRequestSchema, async () => {
  return {
    resources: [
      {
        uri: "file://system",
        mimeType: "application/json",
        name: "File System Operations Interface",
        description: "Interface for performing file system operations"
      }
    ]
  };
});

/**
 * Handler for reading the file system resource
 * This is a placeholder as the actual operations are performed via tools
 */
server.setRequestHandler(ReadResourceRequestSchema, async (request) => {
  if (request.params.uri !== "file://system") {
    throw new McpError(ErrorCode.ResourceNotFound, `Resource ${request.params.uri} not found`);
  }

  return {
    contents: [{
      uri: request.params.uri,
      mimeType: "application/json",
      text: JSON.stringify({
        message: "Use the filesystem tools to perform operations",
        allowedDirectories
      }, null, 2)
    }]
  };
});

/**
 * Handler that lists available tools for filesystem operations
 */
server.setRequestHandler(ListToolsRequestSchema, async () => {
  return {
    tools: [
      {
        name: "read_file",
        description: "Read complete contents of a file",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file"
            }
          },
          required: ["path"]
        }
      },
      {
        name: "read_multiple_files",
        description: "Read multiple files simultaneously",
        inputSchema: {
          type: "object",
          properties: {
            paths: {
              type: "array",
              items: {
                type: "string"
              },
              description: "Array of file paths to read"
            }
          },
          required: ["paths"]
        }
      },
      {
        name: "write_file",
        description: "Create new file or overwrite existing",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file"
            },
            content: {
              type: "string",
              description: "Content to write to the file"
            }
          },
          required: ["path", "content"]
        }
      },
      {
        name: "edit_file",
        description: "Make selective edits using pattern matching",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file"
            },
            edits: {
              type: "array",
              items: {
                type: "object",
                properties: {
                  oldText: {
                    type: "string",
                    description: "Text to search for"
                  },
                  newText: {
                    type: "string",
                    description: "Text to replace with"
                  }
                },
                required: ["oldText", "newText"]
              },
              description: "List of edit operations"
            },
            dryRun: {
              type: "boolean",
              description: "Preview changes without applying"
            }
          },
          required: ["path", "edits"]
        }
      },
      {
        name: "create_directory",
        description: "Create new directory or ensure it exists",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the directory"
            }
          },
          required: ["path"]
        }
      },
      {
        name: "list_directory",
        description: "List directory contents",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the directory"
            }
          },
          required: ["path"]
        }
      },
      {
        name: "move_file",
        description: "Move or rename files and directories",
        inputSchema: {
          type: "object",
          properties: {
            source: {
              type: "string",
              description: "Source path"
            },
            destination: {
              type: "string",
              description: "Destination path"
            }
          },
          required: ["source", "destination"]
        }
      },
      {
        name: "search_files",
        description: "Recursively search for files/directories",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Starting directory"
            },
            pattern: {
              type: "string",
              description: "Search pattern"
            },
            excludePatterns: {
              type: "array",
              items: {
                type: "string"
              },
              description: "Patterns to exclude"
            }
          },
          required: ["path", "pattern"]
        }
      },
      {
        name: "get_file_info",
        description: "Get detailed file/directory metadata",
        inputSchema: {
          type: "object",
          properties: {
            path: {
              type: "string",
              description: "Path to the file or directory"
            }
          },
          required: ["path"]
        }
      },
      {
        name: "list_allowed_directories",
        description: "List all directories the server is allowed to access",
        inputSchema: {
          type: "object",
          properties: {}
        }
      }
    ]
  };
});

/**
 * Handler for filesystem tool operations
 */
server.setRequestHandler(CallToolRequestSchema, async (request) => {
  const { name, arguments: args } = request.params;

  try {
    switch (name) {
      case "read_file": {
        const { path: filePath } = args as { path: string };
        
        if (!isPathAllowed(filePath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${filePath} is not allowed`);
        }
        
        const content = await fs.readFile(filePath, 'utf8');
        
        return {
          content: [{
            type: "text",
            text: content
          }]
        };
      }
      
      case "read_multiple_files": {
        const { paths } = args as { paths: string[] };
        const results: { path: string; content?: string; error?: string }[] = [];
        
        for (const filePath of paths) {
          if (!isPathAllowed(filePath)) {
            results.push({ 
              path: filePath, 
              error: `Access to ${filePath} is not allowed` 
            });
            continue;
          }
          
          try {
            const content = await fs.readFile(filePath, 'utf8');
            results.push({ path: filePath, content });
          } catch (error) {
            results.push({ 
              path: filePath, 
              error: `Error reading file: ${(error as Error).message}` 
            });
          }
        }
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify(results, null, 2)
          }]
        };
      }
      
      case "write_file": {
        const { path: filePath, content } = args as { path: string; content: string };
        
        if (!isPathAllowed(filePath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${filePath} is not allowed`);
        }
        
        // Create directory if it doesn't exist
        const dirPath = path.dirname(filePath);
        await fs.mkdir(dirPath, { recursive: true });
        
        await fs.writeFile(filePath, content);
        
        return {
          content: [{
            type: "text",
            text: `Successfully wrote to ${filePath}`
          }]
        };
      }
      
      case "edit_file": {
        const { path: filePath, edits, dryRun = false } = args as { 
          path: string; 
          edits: { oldText: string; newText: string }[];
          dryRun?: boolean;
        };
        
        if (!isPathAllowed(filePath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${filePath} is not allowed`);
        }
        
        // Read the file
        const originalContent = await fs.readFile(filePath, 'utf8');
        let newContent = originalContent;
        
        // Apply edits
        const results = [];
        for (const edit of edits) {
          const { oldText, newText } = edit;
          if (!newContent.includes(oldText)) {
            results.push({
              match: false,
              oldText,
              message: "Text not found in file"
            });
            continue;
          }
          
          newContent = newContent.replace(oldText, newText);
          results.push({
            match: true,
            oldText,
            newText
          });
        }
        
        // Generate diff
        const diff = generateDiff(originalContent, newContent);
        
        if (!dryRun) {
          await fs.writeFile(filePath, newContent);
        }
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify({
              dryRun,
              path: filePath,
              results,
              diff,
              applied: !dryRun
            }, null, 2)
          }]
        };
      }
      
      case "create_directory": {
        const { path: dirPath } = args as { path: string };
        
        if (!isPathAllowed(dirPath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${dirPath} is not allowed`);
        }
        
        await fs.mkdir(dirPath, { recursive: true });
        
        return {
          content: [{
            type: "text",
            text: `Directory ${dirPath} created or already exists`
          }]
        };
      }
      
      case "list_directory": {
        const { path: dirPath } = args as { path: string };
        
        if (!isPathAllowed(dirPath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${dirPath} is not allowed`);
        }
        
        const entries = await fs.readdir(dirPath, { withFileTypes: true });
        const formattedEntries = entries.map(entry => {
          const prefix = entry.isDirectory() ? "[DIR] " : "[FILE] ";
          return prefix + entry.name;
        });
        
        return {
          content: [{
            type: "text",
            text: formattedEntries.join('\n')
          }]
        };
      }
      
      case "move_file": {
        const { source, destination } = args as { source: string; destination: string };
        
        if (!isPathAllowed(source)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${source} is not allowed`);
        }
        
        if (!isPathAllowed(destination)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${destination} is not allowed`);
        }
        
        // Check if destination exists
        if (existsSync(destination)) {
          throw new McpError(ErrorCode.InvalidRequest, `Destination ${destination} already exists`);
        }
        
        // Create destination directory if it doesn't exist
        const destDir = path.dirname(destination);
        await fs.mkdir(destDir, { recursive: true });
        
        await fs.rename(source, destination);
        
        return {
          content: [{
            type: "text",
            text: `Successfully moved ${source} to ${destination}`
          }]
        };
      }
      
      case "search_files": {
        const { path: dirPath, pattern, excludePatterns = [] } = args as { 
          path: string; 
          pattern: string;
          excludePatterns?: string[];
        };
        
        if (!isPathAllowed(dirPath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${dirPath} is not allowed`);
        }
        
        // Use glob to search for files
        const matches = await glob(`${dirPath}/**/${pattern}`, {
          ignore: excludePatterns,
          nocase: true
        });
        
        // Filter out matches that are not in allowed directories
        const allowedMatches = matches.filter(match => isPathAllowed(match));
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify(allowedMatches, null, 2)
          }]
        };
      }
      
      case "get_file_info": {
        const { path: filePath } = args as { path: string };
        
        if (!isPathAllowed(filePath)) {
          throw new McpError(ErrorCode.PermissionDenied, `Access to ${filePath} is not allowed`);
        }
        
        const stats = await fs.stat(filePath);
        
        const info = {
          path: filePath,
          size: stats.size,
          isDirectory: stats.isDirectory(),
          isFile: stats.isFile(),
          created: stats.birthtime,
          modified: stats.mtime,
          accessed: stats.atime,
          permissions: stats.mode.toString(8).slice(-3)
        };
        
        return {
          content: [{
            type: "text",
            text: JSON.stringify(info, null, 2)
          }]
        };
      }
      
      case "list_allowed_directories": {
        return {
          content: [{
            type: "text",
            text: JSON.stringify(allowedDirectories, null, 2)
          }]
        };
      }
      
      default:
        throw new McpError(ErrorCode.MethodNotFound, `Unknown tool: ${name}`);
    }
  } catch (error) {
    if (error instanceof McpError) {
      throw error;
    }
    
    return {
      content: [{
        type: "text",
        text: `Error: ${(error as Error).message}`
      }],
      isError: true
    };
  }
});

/**
 * Generate a simple diff between two strings
 */
function generateDiff(oldText: string, newText: string): string {
  const oldLines = oldText.split('\n');
  const newLines = newText.split('\n');
  
  let diff = '';
  
  for (let i = 0; i < Math.max(oldLines.length, newLines.length); i++) {
    const oldLine = i < oldLines.length ? oldLines[i] : '';
    const newLine = i < newLines.length ? newLines[i] : '';
    
    if (oldLine !== newLine) {
      if (oldLine) {
        diff += `- ${oldLine}\n`;
      }
      if (newLine) {
        diff += `+ ${newLine}\n`;
      }
    } else {
      diff += `  ${oldLine}\n`;
    }
  }
  
  return diff;
}

/**
 * Start the server using stdio transport
 */
async function main() {
  const transport = new StdioServerTransport();
  await server.connect(transport);
  console.error('Filesystem MCP server running on stdio');
  console.error('Allowed directories:', allowedDirectories);
}

main().catch((error) => {
  console.error("Server error:", error);
  process.exit(1);
});
