import { sveltekit } from '@sveltejs/kit/vite';

/** @type {import('vite').UserConfig} */
const config = {
	plugins: [sveltekit()],
	server: {
        proxy: {
            '/api': 'http://api:5000',
        },
    },
};

export default config;
