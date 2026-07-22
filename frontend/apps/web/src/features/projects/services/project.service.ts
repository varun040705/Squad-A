import { api } from "@/services/api/client";

import {
  Project,
  CreateProjectRequest,
  UpdateProjectRequest,
} from "../types/project";

export const ProjectService = {
  getProjects() {
    return api.get<Project[]>("/projects");
  },

  getProject(id: number) {
    return api.get<Project>(`/projects/${id}`);
  },

  createProject(data: CreateProjectRequest) {
    return api.post<Project>("/projects", data);
  },

  updateProject(
    id: number,
    data: UpdateProjectRequest
  ) {
    return api.put<Project>(
      `/projects/${id}`,
      data
    );
  },

  deleteProject(id: number) {
    return api.delete<void>(
      `/projects/${id}`
    );
  },
};