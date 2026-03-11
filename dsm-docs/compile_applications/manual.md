# Appendix B: Compile Applications Manually

## Compile Applications

The Synology NAS uses embedded SoC or x86-based CPUs across different platforms including ARM and x86 on various models. To run third-party applications on a Synology NAS requires compiling applications into executable formats compatible with the target platform.

### Key Concepts

**Cross-Compilation**: The process of compiling an application on one type of computer system to run on a different type, requiring a compiler that runs on a Linux PC to generate executable files for the Synology NAS.

**Tool Chain**: The set of compiling tools (compiler, linker, etc.) used in the cross-compilation process.

### Resources Referenced

- Reference link: "What kind of CPU does my NAS have" (forum.synology.com)
- DSM tool chain selection depends on the specific Synology NAS model
- Complete model list available in CPU specification documentation

### Subsections

- Download DSM Tool Chain
- Compile
- Compile Open Source Projects
