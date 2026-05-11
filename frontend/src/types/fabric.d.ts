declare module 'fabric' {
  export class Canvas {
    constructor(element: HTMLCanvasElement | string | null, options?: any)
    width: number
    height: number
    selection: boolean
    isDrawingMode: boolean
    freeDrawingBrush: PencilBrush
    setBackgroundImage(image: any, callback: () => void, options?: any): void
    renderAll(): void
    add(...objects: any[]): void
    remove(object: any): void
    getObjects(): any[]
    getPointer(e: MouseEvent): Point
    setActiveObject(object: any): void
    loadFromJSON(json: any, callback?: () => void): void
    toJSON(): any
    on(event: string, handler: (options: any) => void): void
    off(event: string): void
  }

  export class PencilBrush {
    constructor(canvas: Canvas)
    color: string
    width: number
  }

  export class Point {
    x: number
    y: number
    constructor(x: number, y: number)
  }

  export class Line {
    constructor(points: number[], options?: any)
  }

  export class Circle {
    constructor(options?: any)
  }

  export class Triangle {
    constructor(options?: any)
  }

  export class IText {
    constructor(text: string, options?: any)
    enterEditing(): void
  }

  export class Group {
    constructor(objects: any[], options?: any)
  }

  export class Image {
    static fromURL(url: string, callback: (img: Image) => void): void
    width?: number
    height?: number
  }
}
