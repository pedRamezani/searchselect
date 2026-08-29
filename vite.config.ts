import tailwindcss from '@tailwindcss/vite';
import { defineConfig, type UserConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import path from 'path';

export const baseConfig: UserConfig = {
	resolve: {
		alias: {
			$lib: path.resolve('./src/lib').replaceAll('\\', '/')
		}
	},
	plugins: [tailwindcss(), svelte()],
	build: {
		assetsDir: '',
		outDir: './py/searchselect/static/',
		// Start every production build from an empty directory, so a stale
		// `pnpm dev` bundle can never survive into a release. The dev config
		// turns this back off to keep watch rebuilds stable.
		emptyOutDir: true,
		lib: {
			entry: ['./src/main.ts'],
			cssFileName: 'main',
			formats: ['es']
		},
		rollupOptions: {
			output: {
				entryFileNames: `[name].js`,
				chunkFileNames: `[name].js`,
				assetFileNames: `[name].[ext]`
			}
		}
	},
	define: {
		'process.env.NODE_ENV': '"production"'
	}
};

// https://vite.dev/config/
export default defineConfig(baseConfig);
