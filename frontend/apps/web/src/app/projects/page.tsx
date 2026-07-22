"use client";

import { useEffect, useState } from "react";

import Header from "@/components/layout/Header";
import Footer from "@/components/layout/Footer";
import PageContainer from "@/components/layout/PageContainer";

import { ProjectService } from "@/features/projects/services/project.service";
import { Project } from "@/features/projects/types/project";

export default function ProjectsPage() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadProjects();
  }, []);

  async function loadProjects() {
  console.log("Loading projects...");

  try {
    const data = await ProjectService.getProjects();

    console.log("Projects response:", data);
    console.log("Is Array:", Array.isArray(data));
    console.log("Length:", data.length);

    setProjects(data);
  } catch (error) {
    console.error("Project load failed:", error);
  } finally {
    setLoading(false);
  }
}

  return (
    <>
      <Header />

      <PageContainer>
        <h1>Projects</h1>

        {loading ? (
          <p>Loading...</p>
        ) : projects.length === 0 ? (
          <p>No projects found.</p>
        ) : (
          <ul>
            {projects.map((project) => (
              <li key={project.id}>
                <strong>{project.name}</strong>

                <br />

                {project.description}
              </li>
            ))}
          </ul>
        )}
      </PageContainer>

      <Footer />
    </>
  );
}