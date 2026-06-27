<h1>Tap Away </h1>

Tap Away is a logic based 3D puzzle game built from the ground up using Python and Modern OpenGL. Inspired by popular spatial puzzles, the game challenges players to clear a structure of blocks by thinking several steps ahead

 <h2> How to Play</h2>
 
The objective is simple: Clear the entire grid. However, each block has a specific direction it must follow

1. Analyze the Grid: Examine the arrows on each block. A block can only move in the direction its arrow is pointing.
2. Clear the Path: A block will only "Tap Away" if its path is completely unobstructed by other blocks.
3. Rotate for Perspective: Many blocks are hidden or blocked from your current view. You must rotate the puzzle in 3D space to find the next available move.
4. Chain Reactions: Removing one block often opens up paths for several others. Plan your sequence to clear the level efficiently

<h2> Levels of Difficulty</h2>

The game features a procedural generation system that scales the challenge across three distinct modes:

- <strong>Easy</strong>: Small grids (e.g., 3x3x3) with straightforward paths. Perfect for warming up

- <strong>Medium</strong>: Larger structures with more interlocking blocks, requiring more frequent rotation and planning

- <strong>Hard</strong>: Dense, complex 3D structures. At this level, many blocks are buried deep within the core, requiring a precise order of operations to solve

<table>
    <tr>
      <th>Action</th>
      <th>Control</th>
    </tr>
    <tr>
      <td>Tap Block</td>
      <td>Left Click</td>
    </tr>
    <tr>
      <td>Rotate Puzzle</td>
      <td>Right Click + Drag</td>
    </tr>
    <tr>
      <td>Menu Navigation</td>
      <td>Left Click on UI buttons</td>
    </tr>
    <tr>
      <td>Quit Game</td>
      <td>ESC</td>
    </tr>
  </table>

  <h2>Key Features</h2>
  
<strong>Custom 3D Engine</strong>: Built using PyOpenGL and GLFW, featuring custom GLSL shaders for high-performance rendering

<strong>Dynamic UI</strong>: A polished, shader-based interface including real-time stat chips, level progress, and score tracking

<strong>Smooth Animations</strong>: Visual feedback through "wiggles" for blocked moves and smooth flight paths for successful taps

<strong>Campaign Mode</strong>: Progress through levels with increasing complexity and track your total campaign score

<h2> Installation</h2>

<h3>Prerequisites</h3>
<pre>
Python 3.8+
A graphics card supporting OpenGL 3.3+
</pre>

<h4>Setup</h4>

1. Clone the repository:

<pre>
git clone https://github.com/Basliel-Sisay/Tap_Away.git
cd Tap_Away
</pre>

2. Install dependencies:

<pre>
  pip install pyopengl glfw numpy
</pre>

3.Run the game:
<pre>
  python main.py
</pre>

<h2>Tech Stack</h2>

<strong>Language</strong>: Python 3

<strong>Graphics</strong>: PyOpenGL/Modern GL Profile

<strong>Windowing</strong>: GLFW

<strong>Mathematics</strong>: NumPy and Custom 3D Math Library (Quaternions/Matrices)

<h2>Section 2 Group Members</h2>

<table>
    <tr>
      <th>Name</th>
      <th>ID</th>
    </tr>
    <tr>
      <td>Basliel Sisay</td>
      <td>UGR/3563/16</td>
    </tr>
    <tr>
      <td>Bontu Kedir</td>
      <td>UGR/7760/16</td>
    </tr>
    <tr>
      <td>Naol Worku</td>
      <td>UGR/7914/16</td>
    </tr>
    <tr>
      <td>Semhal Habte</td>
      <td>UGR/7889/16</td>
    </tr>
    <tr>
      <td>Tsion Alemu</td>
      <td>UGR/8861/16</td>
    </tr>
    <tr>
      <td>Victory Bedru</td>
      <td>UGR/4541/16</td>
    </tr>
  </table>
