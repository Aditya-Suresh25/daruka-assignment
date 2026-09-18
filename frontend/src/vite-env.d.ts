/// <reference types="vite/client" />
declare module '@mapbox/mapbox-gl-draw' {
	export default class MapboxDraw {
		constructor(options?: { displayControlsDefault?: boolean; controls?: { polygon?: boolean; trash?: boolean } })
	}
}
